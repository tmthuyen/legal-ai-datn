"""
import_neo4j.py
Script nạp dữ liệu Knowledge Graph pháp lý vào cơ sở dữ liệu Neo4j.

Quy trình thực hiện:
1. Đọc dữ liệu từ backend/data/processed/ (nodes.json và relations.json).
2. Kiểm tra tính hợp lệ toàn vẹn của dữ liệu bằng KnowledgeGraphSyncVerifier (Pre-import Validation).
   Bắt buộc trạng thái PASS (kể cả WARN cũng bị chặn). Nếu có lỗi, script DỪNG NGAY và KHÔNG kết nối/ghi Neo4j.
3. Đảm bảo Unique Constraint cho node_id trên nhãn :LegalNode.
4. Nạp Nodes và Relationships trong MỘT TRANSACTION DUY NHẤT (Single Write Transaction).
5. Deep Transaction Verification: Trước khi commit transaction, đối chiếu toàn bộ node IDs, labels,
   properties, relationship keys và properties. Nếu phát hiện bất kỳ sai khác nào, rollback toàn bộ.
"""

import argparse
from collections import defaultdict
import json
import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

# Cấu hình UTF-8 cho Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_backend_dir() -> pathlib.Path:
    current = pathlib.Path(__file__).resolve()
    for p in current.parents:
        if p.name == "backend" or (p / "data" / "processed").exists():
            return p
    return current.parents[3]


BACKEND_DIR = find_backend_dir()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ENV_PATH = BACKEND_DIR / ".env"
DATA_DIR = BACKEND_DIR / "data" / "processed"
NODES_FILE = DATA_DIR / "nodes.json"
RELATIONS_FILE = DATA_DIR / "relations.json"

from src.graph.sync_verifier import KnowledgeGraphSyncVerifier


class Neo4jLegalImporter:
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j", batch_size: int = 1000):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.batch_size = batch_size
        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

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

    def preflight_validate(
        self,
        nodes_path: Optional[pathlib.Path] = None,
        relations_path: Optional[pathlib.Path] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Xác thực toàn bộ cấu trúc đồ thị trước khi import bằng KnowledgeGraphSyncVerifier."""
        n_file = pathlib.Path(nodes_path) if nodes_path else NODES_FILE
        r_file = pathlib.Path(relations_path) if relations_path else RELATIONS_FILE

        verifier = KnowledgeGraphSyncVerifier(backend_dir=BACKEND_DIR)
        val_res = verifier.validate_graph_data(nodes_path=n_file, relations_path=r_file)

        if val_res["status"] != "PASS":
            print("\n" + "=" * 80)
            print("❌ [PREFLIGHT THẤT BẠI] DỮ LIỆU ĐỒ THỊ KHÔNG HỢP LỆ!")
            print("=" * 80)
            for err in val_res["errors"]:
                print(f"  - {err}")
            print(">> Đã CHẶN toàn bộ kết nối và thao tác import Neo4j để đảm bảo an toàn cơ sở dữ liệu.")
            raise ValueError(
                f"Preflight requires PASS (got {val_res['status']}); errors={len(val_res['errors'])}; "
                f"warnings={len(val_res['warnings'])}. " + "; ".join(val_res["warnings"][:5])
            )

        if val_res["warnings"]:
            print(f"\n⚠️ [PREFLIGHT CẢNH BÁO] Có {len(val_res['warnings'])} cảnh báo:")
            for w in val_res["warnings"][:5]:
                print(f"  - {w}")

        with open(n_file, "r", encoding="utf-8") as f:
            nodes = json.load(f)
        with open(r_file, "r", encoding="utf-8") as f:
            relations = json.load(f)

        print(f">> [PREFLIGHT THÀNH CÔNG] Đạt chuẩn 100%! Đã xác thực {len(nodes):,} nodes và {len(relations):,} relations.")
        return nodes, relations

    def clear_database(self, confirm: bool = False):
        """Xóa toàn bộ dữ liệu đồ thị hiện tại (chỉ dùng khi truyền kèm cờ --confirm-clear-production-db)."""
        if not confirm:
            raise RuntimeError(
                "[AN TOÀN BẢO VỆ] Cờ --clear-db yêu cầu xác nhận rõ ràng với --confirm-clear-production-db. "
                "Tuyệt đối không xóa database trong quy trình mở rộng thông thường!"
            )
        print("\n[CẢNH BÁO CAO ĐỘ] Đang tiến hành xóa toàn bộ nodes và relationships trong Neo4j database...")
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n:LegalNode) DETACH DELETE n")
        print(">> Đã làm sạch database.")

    def import_nodes(self, nodes: List[Dict[str, Any]]):
        """Nạp nodes vào Neo4j (phương thức phụ trợ backward-compatibility)."""
        print("\n--- BẮT ĐẦU IMPORT NODES ---")
        start_time = time.time()

        nodes_by_type = defaultdict(list)
        for n in nodes:
            ntype = n.get("type") or n.get("label")
            props = self._properties(n, ("type", "label"))
            nodes_by_type[ntype].append({
                "node_id": n["node_id"],
                "props": props,
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
                count = len(type_nodes)
                for i in range(0, count, self.batch_size):
                    batch = type_nodes[i:i + self.batch_size]
                    session.run(cypher, batch=batch)

                total_imported += count
                print(f"  + Đã nạp (:LegalNode:{ntype:<12}): {count:>5,} nodes")

        elapsed = time.time() - start_time
        print(f">> Hoàn thành nạp {total_imported:,} nodes trong {elapsed:.2f}s!")

    def import_relations(self, relations: List[Dict[str, Any]]):
        """Nạp relations vào Neo4j (phương thức phụ trợ backward-compatibility)."""
        print("\n--- BẮT ĐẦU IMPORT RELATIONSHIPS ---")
        start_time = time.time()

        rels_by_type = defaultdict(list)
        for r in relations:
            rtype = r.get("type")
            props = self._properties(r, ("type", "source_id", "target_id", "from", "to"))
            rels_by_type[rtype].append({
                "source_id": r.get("source_id") or r.get("from"),
                "target_id": r.get("target_id") or r.get("to"),
                "props": props,
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

    @staticmethod
    def _properties(source: Dict[str, Any], excluded: tuple) -> Dict[str, Any]:
        """Chuẩn hóa thuộc tính: bỏ các giá trị None và các trường topology."""
        return {k: v for k, v in source.items() if k not in excluded and v is not None}

    @staticmethod
    def _normalized(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    def _verify_in_transaction(self, tx, expected_nodes: List[Dict[str, Any]], expected_relations: List[Dict[str, Any]]):
        """Kiểm tra toàn bộ snapshot bên trong transaction trước khi commit; nếu sai khác sẽ rollback."""
        db_nodes = tx.run("MATCH (n:LegalNode) RETURN n.node_id AS id, labels(n) AS labels, properties(n) AS props").data()
        expected_by_id = {n["node_id"]: n for n in expected_nodes}
        actual_by_id = {r["id"]: r for r in db_nodes}

        if set(expected_by_id) != set(actual_by_id):
            missing = list(set(expected_by_id) - set(actual_by_id))[:5]
            extra = list(set(actual_by_id) - set(expected_by_id))[:5]
            raise RuntimeError(f"Node ID mismatch: missing={missing}, extra={extra}")

        for nid, node in expected_by_id.items():
            actual = actual_by_id[nid]
            expected_type = node.get("type") or node.get("label")
            if set(actual["labels"]) != {"LegalNode", expected_type}:
                raise RuntimeError(f"Node labels mismatch at {nid}: {actual['labels']}")
            expected_props = self._properties(node, ("type", "label"))
            if self._normalized(expected_props) != self._normalized(actual["props"]):
                raise RuntimeError(f"Node properties mismatch at {nid}")

        db_rels = tx.run("""MATCH (s:LegalNode)-[r]->(t:LegalNode)
            RETURN s.node_id AS source_id, type(r) AS rel_type, t.node_id AS target_id, properties(r) AS props
        """).data()
        actual_rel = {(r["source_id"], r["rel_type"], r["target_id"]): r["props"] for r in db_rels}
        expected_rel = {}
        for r in expected_relations:
            key = (r.get("source_id") or r.get("from"), r["type"], r.get("target_id") or r.get("to"))
            if key in expected_rel:
                raise RuntimeError(f"Duplicate relation in JSON: {key}")
            expected_rel[key] = self._properties(r, ("type", "source_id", "target_id", "from", "to"))

        if set(actual_rel) != set(expected_rel):
            missing = list(set(expected_rel) - set(actual_rel))[:5]
            extra = list(set(actual_rel) - set(expected_rel))[:5]
            raise RuntimeError(f"Relationship mismatch: missing={missing}, extra={extra}")

        for key, props in expected_rel.items():
            if self._normalized(props) != self._normalized(actual_rel[key]):
                raise RuntimeError(f"Relationship properties mismatch at {key}")

        return {"nodes": len(expected_by_id), "relationships": len(expected_rel)}

    def _verify_transaction(self, tx, expected_nodes: List[Dict[str, Any]], expected_relations: List[Dict[str, Any]]):
        """Bí danh phục vụ kiểm thử và tương thích giao diện transaction verify."""
        return self._verify_in_transaction(tx, expected_nodes, expected_relations)

    def atomic_import(self, nodes: List[Dict[str, Any]], relations: List[Dict[str, Any]], *, clear_db: bool = False):
        """Thực hiện toàn bộ quá trình nạp và xác thực trong MỘT WRITE TRANSACTION DUY NHẤT.
        Không có trạng thái trung gian dở dang nào nếu bất kỳ bước nào thất bại.
        """
        allowed_node_types = {
            "Document", "Part", "Chapter", "Section", "SubSection",
            "Article", "Clause", "Point", "Precedent"
        }
        allowed_rel_types = {
            "CONTAINS", "REFERENCES", "IMPLEMENTS", "INTERPRETED_BY",
            "AMENDS", "REPEALS", "REPLACED_BY", "RELATED_TO"
        }

        nodes_by_type = defaultdict(list)
        rels_by_type = defaultdict(list)

        for n in nodes:
            ntype = n.get("type") or n.get("label")
            if ntype not in allowed_node_types:
                raise ValueError(f"Unsafe node label: {ntype}")
            nodes_by_type[ntype].append({
                "node_id": n["node_id"],
                "props": self._properties(n, ("type", "label")),
            })

        for r in relations:
            rtype = r.get("type")
            if rtype not in allowed_rel_types:
                raise ValueError(f"Unsafe relationship type: {rtype}")
            rels_by_type[rtype].append({
                "source_id": r.get("source_id") or r.get("from"),
                "target_id": r.get("target_id") or r.get("to"),
                "props": self._properties(r, ("type", "source_id", "target_id", "from", "to")),
            })

        def write_and_verify(tx):
            if clear_db:
                tx.run("MATCH (n:LegalNode) DETACH DELETE n").consume()

            for ntype, rows in nodes_by_type.items():
                for i in range(0, len(rows), self.batch_size):
                    tx.run(f"""UNWIND $batch AS row
                        MERGE (n:LegalNode {{node_id: row.node_id}})
                        SET n:{ntype}
                        SET n = row.props
                    """, batch=rows[i:i + self.batch_size]).consume()

            for rtype, rows in rels_by_type.items():
                for i in range(0, len(rows), self.batch_size):
                    tx.run(f"""UNWIND $batch AS row
                        MATCH (s:LegalNode {{node_id: row.source_id}})
                        MATCH (t:LegalNode {{node_id: row.target_id}})
                        MERGE (s)-[r:{rtype}]->(t)
                        SET r = row.props
                    """, batch=rows[i:i + self.batch_size]).consume()

            return self._verify_transaction(tx, nodes, relations)

        with self.driver.session(database=self.database) as session:
            return session.execute_write(write_and_verify)

    def verify_database(self, expected_nodes: List[Dict[str, Any]], expected_relations: List[Dict[str, Any]]):
        with self.driver.session(database=self.database) as session:
            return session.execute_read(self._verify_in_transaction, expected_nodes, expected_relations)


def main():
    parser = argparse.ArgumentParser(description="Import Legal Knowledge Graph vào Neo4j")
    parser.add_argument("--batch-size", type=int, default=1000, help="Kích thước batch import (mặc định: 1000)")
    parser.add_argument("--clear-db", action="store_true", help="Xóa dữ liệu cũ trước khi nạp mới")
    parser.add_argument(
        "--confirm-clear-production-db",
        action="store_true",
        help="Cờ bắt buộc xác nhận để thực thi --clear-db (ngăn chặn thao tác xóa ngoài ý muốn).",
    )
    parser.add_argument("--nodes-file", type=str, default=None, help="Đường dẫn file nodes.json tùy chọn")
    parser.add_argument("--relations-file", type=str, default=None, help="Đường dẫn file relations.json tùy chọn")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chế độ kiểm thử an toàn: chỉ chạy preflight validation, tuyệt đối không kết nối/ghi vào Neo4j",
    )
    args = parser.parse_args()

    nodes_file = pathlib.Path(args.nodes_file) if args.nodes_file else NODES_FILE
    relations_file = pathlib.Path(args.relations_file) if args.relations_file else RELATIONS_FILE

    # Kiểm tra bảo vệ đối với --clear-db
    if args.clear_db:
        if not args.confirm_clear_production_db:
            print(
                "\n[AN TOÀN BẢO VỆ] Cờ --clear-db yêu cầu cờ xác nhận rõ ràng: --confirm-clear-production-db.\n"
                "Thao tác xóa đã bị hủy bỏ để bảo vệ toàn vẹn dữ liệu."
            )
            sys.exit(1)

    load_dotenv(ENV_PATH)
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not args.dry_run and not password:
        parser.error("NEO4J_PASSWORD must be set in the environment or backend/.env")

    importer = Neo4jLegalImporter(uri, user, password or "", database, batch_size=args.batch_size)

    # Chế độ DRY-RUN: Preflight validation duy nhất, không đụng tới Neo4j
    if args.dry_run:
        print(">> [DRY-RUN] Tiến hành Preflight Validation dữ liệu đồ thị (KHÔNG kết nối Neo4j):")
        try:
            nodes, relations = importer.preflight_validate(nodes_file, relations_file)
            print(f">> [DRY-RUN KẾT QUẢ: PASS] Dữ liệu hoàn toàn hợp lệ ({len(nodes):,} nodes, {len(relations):,} relations).")
            sys.exit(0)
        except Exception as e:
            print(f">> [DRY-RUN KẾT QUẢ: FAIL] Lỗi xác thực: {e}")
            sys.exit(1)

    # Chế độ LIVE ATOMIC IMPORT
    print(f">> Cấu hình kết nối: URI={uri}, User={user}, Database={database}")
    try:
        # 1. Bắt buộc Preflight validation trước khi kết nối ghi
        nodes, relations = importer.preflight_validate(nodes_file, relations_file)

        # 2. Kết nối Neo4j
        if not importer.test_connection():
            print("[LỖI] Neo4j không phản hồi. Import dừng lại.")
            sys.exit(1)

        importer.ensure_constraints()

        # Atomic import + full verification before commit; rollback on any mismatch.
        counts = importer.atomic_import(nodes, relations, clear_db=args.clear_db)
        print(f">> [COMMIT] Verified {counts['nodes']} nodes and {counts['relationships']} relationships atomically.")

    except Exception as e:
        print(f"\n❌ [IMPORT THẤT BẠI]: {e}")
        sys.exit(1)
    finally:
        importer.close()


if __name__ == "__main__":
    main()
