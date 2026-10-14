"""
import_neo4j.py
Script nạp dữ liệu Knowledge Graph pháp lý vào cơ sở dữ liệu Neo4j.

Quy trình thực hiện:
1. Đọc dữ liệu từ backend/data/processed/ (nodes.json và relations.json).
2. Kiểm tra tính hợp lệ của dữ liệu trước khi nạp (Pre-import Validation).
3. Đảm bảo Constraint duy nhất cho node_id trên label :LegalNode.
4. Nạp Nodes theo thứ tự cấu trúc với đa nhãn (:LegalNode:<Type>), sử dụng batching + MERGE.
5. Nạp Relationships (:CONTAINS, :REFERENCES), sử dụng batching + MERGE (không tự sinh từ parent_id).
6. Truy vấn đối chiếu số liệu thực tế trong Neo4j để đảm bảo tính toàn vẹn 100%.
"""

import os
import sys
import json
import time
import argparse
import pathlib
from collections import defaultdict, Counter
from typing import List, Dict, Any

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver

# Cấu hình UTF-8 cho Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Đường dẫn mặc định
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'
DATA_DIR = BASE_DIR / 'data' / 'processed'
NODES_FILE = DATA_DIR / 'nodes.json'
RELATIONS_FILE = DATA_DIR / 'relations.json'

# Whitelist Labels và Types hợp lệ
ALLOWED_NODE_TYPES = {
    'Document', 'Part', 'Chapter', 'Section', 'SubSection', 
    'Article', 'Clause', 'Point', 'Precedent'
}
ALLOWED_REL_TYPES = {
    'CONTAINS', 'REFERENCES', 'IMPLEMENTS', 'INTERPRETED_BY', 
    'AMENDS', 'REPEALS', 'REPLACED_BY', 'RELATED_TO'
}


class Neo4jLegalImporter:
    def __init__(self, uri: str, user: str, password: str, database: str = 'neo4j', batch_size: int = 1000):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.batch_size = batch_size
        self.driver: Driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        if self.driver:
            self.driver.close()

    def test_connection(self) -> bool:
        """Kiểm tra kết nối tới cơ sở dữ liệu Neo4j."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS connected")
                record = result.single()
                return record and record["connected"] == 1
        except Exception as e:
            print(f"[LỖI] Không thể kết nối tới Neo4j ({self.uri}): {e}")
            return False

    def ensure_constraints(self):
        """Khởi tạo Unique Constraint trên node_id của label LegalNode nếu chưa tồn tại."""
        cypher = """
        CREATE CONSTRAINT legal_node_id_unique IF NOT EXISTS
        FOR (n:LegalNode) REQUIRE n.node_id IS UNIQUE
        """
        with self.driver.session(database=self.database) as session:
            session.run(cypher)
            print(">> Đã xác nhận Unique Constraint: (n:LegalNode) REQUIRE n.node_id IS UNIQUE")

    def validate_files(self) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Đọc và kiểm tra sơ bộ các file JSON trước khi import."""
        if not NODES_FILE.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {NODES_FILE}")
        if not RELATIONS_FILE.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {RELATIONS_FILE}")

        with open(NODES_FILE, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
        with open(RELATIONS_FILE, 'r', encoding='utf-8') as f:
            relations = json.load(f)

        print(f">> Đọc thành công {len(nodes):,} nodes từ {NODES_FILE.name}")
        print(f">> Đọc thành công {len(relations):,} relations từ {RELATIONS_FILE.name}")

        # Kiểm tra tính hợp lệ của node_id
        node_ids = set()
        for idx, n in enumerate(nodes):
            nid = n.get('node_id')
            ntype = n.get('type')
            if not nid:
                raise ValueError(f"Node tại vị trí {idx} thiếu 'node_id'")
            if ntype not in ALLOWED_NODE_TYPES:
                raise ValueError(f"Node {nid} có type không hợp lệ: '{ntype}'")
            if nid in node_ids:
                raise ValueError(f"Trùng lặp node_id trong file: '{nid}'")
            node_ids.add(nid)

        # Kiểm tra tính hợp lệ của relation
        for idx, r in enumerate(relations):
            sid = r.get('source_id')
            tid = r.get('target_id')
            rtype = r.get('type')
            if not sid or not tid or not rtype:
                raise ValueError(f"Relation tại vị trí {idx} thiếu source_id, target_id hoặc type")
            if rtype not in ALLOWED_REL_TYPES:
                raise ValueError(f"Relation tại vị trí {idx} có type không hợp lệ: '{rtype}'")
            if sid not in node_ids:
                raise ValueError(f"Relation có source_id không tồn tại: '{sid}'")
            if tid not in node_ids:
                raise ValueError(f"Relation có target_id không tồn tại: '{tid}'")

        print(">> Kiểm tra dữ liệu: ĐẠT CHUẨN 100%! Sẵn sàng import.")
        return nodes, relations

    def clear_database(self):
        """Xóa toàn bộ dữ liệu đồ thị hiện tại (chỉ dùng khi truyền cờ --clear-db)."""
        print("\n[CẢNH BÁO] Đang tiến hành xóa toàn bộ nodes và relationships trong database...")
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n:LegalNode) DETACH DELETE n")
        print(">> Đã làm sạch database.")

    def import_nodes(self, nodes: List[Dict[str, Any]]):
        """
        Nạp nodes vào Neo4j:
        - Sử dụng đa nhãn: (:LegalNode:<Type>)
        - Phân nhóm theo type để tối ưu hóa execution plan và batching.
        - Dùng MERGE để đảm bảo tính Idempotent (chạy lại nhiều lần không trùng).
        """
        print("\n--- BẮT ĐẦU IMPORT NODES ---")
        start_time = time.time()

        # Phân loại nodes theo type
        nodes_by_type = defaultdict(list)
        for n in nodes:
            ntype = n.get('type')
            # Lọc bỏ các giá trị None để tránh gán null thừa
            props = {k: v for k, v in n.items() if v is not None and k != 'type'}
            nodes_by_type[ntype].append({
                'node_id': n['node_id'],
                'props': props
            })

        total_imported = 0
        with self.driver.session(database=self.database) as session:
            for ntype, type_nodes in nodes_by_type.items():
                cypher = f"""
                UNWIND $batch AS row
                MERGE (n:LegalNode {{node_id: row.node_id}})
                SET n:{ntype}
                SET n += row.props
                """
                
                # Chia batch
                count = len(type_nodes)
                for i in range(0, count, self.batch_size):
                    batch = type_nodes[i:i + self.batch_size]
                    session.run(cypher, batch=batch)
                
                total_imported += count
                print(f"  + Đã nạp (:LegalNode:{ntype:<12}): {count:>5,} nodes")

        elapsed = time.time() - start_time
        print(f">> Hoàn thành nạp {total_imported:,} nodes trong {elapsed:.2f}s!")

    def import_relations(self, relations: List[Dict[str, Any]]):
        """
        Nạp relations vào Neo4j:
        - Phân nhóm theo relation type (:CONTAINS, :REFERENCES).
        - Nối giữa các (s:LegalNode)-[:TYPE]->(t:LegalNode) thông qua node_id.
        - Dùng MERGE để đảm bảo tính Idempotent (không tạo cạnh duplicate khi chạy lại).
        """
        print("\n--- BẮT ĐẦU IMPORT RELATIONSHIPS ---")
        start_time = time.time()

        # Phân loại relations theo type
        rels_by_type = defaultdict(list)
        for r in relations:
            rtype = r.get('type')
            props = {
                k: v for k, v in r.items() 
                if v is not None and k not in ('source_id', 'target_id', 'type')
            }
            rels_by_type[rtype].append({
                'source_id': r['source_id'],
                'target_id': r['target_id'],
                'props': props
            })

        total_imported = 0
        with self.driver.session(database=self.database) as session:
            for rtype, type_rels in rels_by_type.items():
                cypher = f"""
                UNWIND $batch AS row
                MATCH (s:LegalNode {{node_id: row.source_id}})
                MATCH (t:LegalNode {{node_id: row.target_id}})
                MERGE (s)-[r:{rtype}]->(t)
                SET r += row.props
                """
                
                count = len(type_rels)
                for i in range(0, count, self.batch_size):
                    batch = type_rels[i:i + self.batch_size]
                    session.run(cypher, batch=batch)
                    
                total_imported += count
                print(f"  + Đã nạp [:{rtype:<14}]: {count:>5,} quan hệ")

        elapsed = time.time() - start_time
        print(f">> Hoàn thành nạp {total_imported:,} relations trong {elapsed:.2f}s!")

    def verify_database(self, expected_node_count: int, expected_rel_count: int):
        """Truy vấn kiểm tra đối chiếu trực tiếp dữ liệu thực tế trong Neo4j."""
        print("\n====================================================================")
        print("          KẾT QUẢ ĐỐI CHIẾU DỮ LIỆU THỰC TẾ TRONG NEO4J")
        print("====================================================================")
        
        with self.driver.session(database=self.database) as session:
            # 1. Đếm tổng số nodes
            res_nodes = session.run("MATCH (n:LegalNode) RETURN count(n) AS total").single()
            actual_nodes = res_nodes["total"] if res_nodes else 0
            
            # 2. Đếm số lượng từng loại node
            res_labels = session.run("""
            MATCH (n:LegalNode)
            UNWIND labels(n) AS lbl
            WITH lbl, count(*) AS cnt
            WHERE lbl <> 'LegalNode'
            RETURN lbl, cnt ORDER BY cnt DESC
            """)
            print(f"Tổng số nodes (:LegalNode) trong DB: {actual_nodes:,} (Kỳ vọng: {expected_node_count:,})")
            for r in res_labels:
                print(f"  - {r['lbl']:<15}: {r['cnt']:,}")

            # 3. Đếm tổng số relationships
            res_rels = session.run("MATCH (:LegalNode)-[r]->(:LegalNode) RETURN count(r) AS total").single()
            actual_rels = res_rels["total"] if res_rels else 0
            
            # 4. Đếm số lượng từng loại relationship
            res_types = session.run("""
            MATCH (:LegalNode)-[r]->(:LegalNode)
            RETURN type(r) AS rel_type, count(r) AS cnt ORDER BY cnt DESC
            """)
            print(f"\nTổng số relations trong DB: {actual_rels:,} (Kỳ vọng: {expected_rel_count:,})")
            for r in res_types:
                print(f"  - {r['rel_type']:<15}: {r['cnt']:,}")

            print("====================================================================")
            if actual_nodes == expected_node_count and actual_rels == expected_rel_count:
                print(">> XÁC NHẬN: DỮ LIỆU TRONG NEO4J KHỚP CHÍNH XÁC 100% VỚI FILE JSON!")
            else:
                print("[CẢNH BÁO] Có sự chênh lệch giữa số lượng trong DB và file JSON!")


def main():
    parser = argparse.ArgumentParser(description="Import Legal Knowledge Graph vào Neo4j")
    parser.add_argument("--batch-size", type=int, default=1000, help="Kích thước batch import (mặc định: 1000)")
    parser.add_argument("--clear-db", action="store_true", help="Xóa dữ liệu cũ trước khi nạp mới")
    args = parser.parse_args()

    # Load biến môi trường từ .env
    load_dotenv(ENV_PATH)
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'thang123')
    database = os.getenv('NEO4J_DATABASE', 'neo4j')

    print(f">> Cấu hình kết nối: URI={uri}, User={user}, Database={database}")
    importer = Neo4jLegalImporter(uri, user, password, database, batch_size=args.batch_size)

    try:
        if not importer.test_connection():
            sys.exit(1)

        importer.ensure_constraints()
        nodes, relations = importer.validate_files()

        if args.clear_db:
            importer.clear_database()

        importer.import_nodes(nodes)
        importer.import_relations(relations)
        importer.verify_database(len(nodes), len(relations))

    finally:
        importer.close()


if __name__ == '__main__':
    main()
