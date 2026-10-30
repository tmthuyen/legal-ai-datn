"""
sync_verifier.py
Module kiểm tra tính toàn vẹn của Knowledge Graph và đối soát đồng bộ đa tầng
giữa nodes.json, relations.json, Neo4j, BM25, ChromaDB, và NPZ cache trước và sau khi mở rộng văn bản luật.
"""

from collections import Counter, defaultdict
import datetime
import hashlib
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

ALLOWED_NODE_TYPES = {
    "Document", "Part", "Chapter", "Section", "SubSection",
    "Article", "Clause", "Point", "Precedent"
}

ALLOWED_REL_TYPES = {
    "CONTAINS", "REFERENCES", "IMPLEMENTS", "INTERPRETED_BY",
    "AMENDS", "REPEALS", "REPLACED_BY", "RELATED_TO"
}

# Quy định chặt chẽ cấu trúc phân cấp pháp luật hợp lệ (Legal Hierarchy Invariants)
ALLOWED_PARENT_TYPES = {
    "Document": set(),  # Document là đỉnh cây, parent_id bắt buộc là None
    "Part": {"Document"},
    "Chapter": {"Document", "Part"},
    "Section": {"Chapter"},
    "SubSection": {"Section"},
    "Article": {"Document", "Part", "Chapter", "Section", "SubSection"},
    "Clause": {"Article"},
    "Point": {"Clause", "Article"},
    "Precedent": {"Document"},
}

KNOWN_MODEL_DIMENSIONS = {
    "darklethelong/vnlegal-lal": 1024,
    "BAAI/bge-m3": 1024,
    "Aura/Aura-Embedding": 768,
    "bkai-foundation-models/vietnamese-bi-encoder": 768,
}


def compute_article_corpus_hash(articles: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> str:
    """Tính SHA256 mã băm ngữ liệu chuẩn theo enriched text của Article nodes."""
    from src.graph.embedder import build_enriched_text
    from src.vector.embedding_pipeline import compute_corpus_hash

    # Sắp xếp các node theo node_id tăng dần để đảm bảo tính tất định
    sorted_articles = sorted(articles, key=lambda x: str(x.get("node_id", "")))
    node_ids = [str(a.get("node_id", "")) for a in sorted_articles]
    texts = [build_enriched_text(a, node_map) if node_map else str(a.get("full_text") or a.get("text") or "") for a in sorted_articles]

    return compute_corpus_hash(node_ids, texts)


class KnowledgeGraphSyncVerifier:
    """Bộ công cụ kiểm định Knowledge Graph và kiểm tra tính đồng bộ Retrieval đa tầng."""

    def __init__(self, backend_dir: Optional[Path] = None):
        if backend_dir is None:
            backend_dir = Path(__file__).resolve().parents[2]
        self.backend_dir = Path(backend_dir)
        self.data_dir = self.backend_dir / "data" / "processed"
        self.chroma_path = self.backend_dir / "data" / "chroma"
        self.unres_refs_path = self.data_dir / "unresolved_references.json"
        self.unres_docs_path = self.data_dir / "unresolved_document_relations.json"

        # Đọc cấu hình động từ get_settings() nếu có thể
        try:
            from src.common.setting_config import get_settings
            settings = get_settings()
            self.expected_model_name = settings.embedding_model_name
            self.expected_dimension = KNOWN_MODEL_DIMENSIONS.get(self.expected_model_name, 1024)
            self.target_chroma_collection = settings.chroma_collection
            self.active_vector_backend = settings.vector_backend
            slug = self.expected_model_name.replace("/", "_")
            self.npz_path = self.backend_dir / "data" / "embeddings" / f"article_embeddings_{slug}_enriched.npz"
        except Exception:
            self.expected_model_name = "darklethelong/vnlegal-lal"
            self.expected_dimension = 1024
            self.target_chroma_collection = "legal_articles"
            self.active_vector_backend = "chroma"
            self.npz_path = (
                self.backend_dir
                / "data"
                / "embeddings"
                / "article_embeddings_darklethelong_vnlegal-lal_enriched.npz"
            )

    # =========================================================================
    # 1. KIỂM ĐỊNH TÍNH TOÀN VẸN CỦA ĐỒ THỊ (GRAPH DATA VALIDATION)
    # =========================================================================
    def validate_graph_data(
        self,
        nodes_path: Optional[Path] = None,
        relations_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Kiểm tra schema, duplicate IDs, missing parents, cycle bất kỳ độ sâu,
        tính nhất quán giữa cây parent_id và quan hệ CONTAINS trong relations.json.

        Args:
            nodes_path: Đường dẫn file nodes.json (mặc định data/processed/nodes.json).
            relations_path: Đường dẫn file relations.json (mặc định data/processed/relations.json).

        Returns:
            Dict chứa trạng thái (PASS/FAIL/WARN), danh sách lỗi, cảnh báo và thống kê chi tiết.
        """
        n_path = Path(nodes_path) if nodes_path else self.data_dir / "nodes.json"
        r_path = Path(relations_path) if relations_path else self.data_dir / "relations.json"

        errors: List[str] = []
        warnings: List[str] = []

        if not n_path.exists():
            return {
                "status": "FAIL",
                "errors": [f"Không tìm thấy file nodes: {n_path}"],
                "warnings": [],
                "statistics": {},
            }

        with open(n_path, "r", encoding="utf-8") as f:
            nodes = json.load(f)

        relations = []
        if r_path.exists():
            with open(r_path, "r", encoding="utf-8") as f:
                relations = json.load(f)
        else:
            errors.append(f"Không tìm thấy file relations: {r_path}")

        # 1.1 Kiểm tra trùng lặp node_id & phân loại
        seen_ids: Set[str] = set()
        duplicate_ids: List[str] = []
        node_map: Dict[str, Dict[str, Any]] = {}
        invalid_types: List[Tuple[str, str]] = []
        naming_format_warnings: List[Tuple[str, str]] = []

        type_counts = Counter()
        for idx, n in enumerate(nodes):
            nid = n.get("node_id")
            ntype = n.get("type") or n.get("label")

            if not nid:
                errors.append(f"Node tại chỉ mục {idx} thiếu 'node_id'.")
                continue

            if nid in seen_ids:
                duplicate_ids.append(nid)
            seen_ids.add(nid)
            node_map[nid] = n

            if ntype not in ALLOWED_NODE_TYPES:
                invalid_types.append((nid, str(ntype)))
            else:
                type_counts[ntype] += 1

            # Kiểm tra quy ước định danh Article
            if ntype == "Article":
                if "_D" not in nid:
                    naming_format_warnings.append((nid, "Article node_id không tuân thủ mẫu {DOC_ID}_D{number}"))
                if not n.get("full_text") and not n.get("text"):
                    warnings.append(f"Article {nid} không có nội dung text/full_text.")

        if duplicate_ids:
            errors.append(f"Phát hiện {len(duplicate_ids)} node_id bị trùng lặp: {duplicate_ids[:10]}")
        if invalid_types:
            errors.append(f"Phát hiện {len(invalid_types)} node có type không hợp lệ: {invalid_types[:5]}")

        # 1.2 Kiểm tra quan hệ parent-child, cấu trúc phân cấp và document_id đồng nhất
        missing_parents: List[Tuple[str, str, str]] = []
        invalid_hierarchy: List[Tuple[str, str, str, str]] = []
        document_mismatches: List[Tuple[str, str, str, str]] = []

        for nid, n in node_map.items():
            ntype = n.get("type") or n.get("label")
            pid = n.get("parent_id")
            doc_id = n.get("document_id")

            if ntype == "Document":
                if pid is not None:
                    warnings.append(f"Node Document {nid} có parent_id: {pid} (nên là None).")
                continue

            if not pid:
                errors.append(f"Node {ntype} '{nid}' thiếu thuộc tính 'parent_id'.")
                continue

            if pid not in node_map:
                missing_parents.append((nid, ntype, pid))
                continue

            parent_node = node_map[pid]
            ptype = parent_node.get("type") or parent_node.get("label")

            # Kiểm tra loại cha có hợp lệ theo phân cấp pháp luật không
            allowed_p = ALLOWED_PARENT_TYPES.get(ntype, set())
            if ptype not in allowed_p:
                invalid_hierarchy.append((nid, ntype, pid, str(ptype)))

            # Kiểm tra đồng nhất document_id giữa con và cha
            parent_doc_id = parent_node.get("document_id")
            if ptype == "Document":
                expected_doc_id = parent_doc_id or parent_node.get("node_id")
            else:
                expected_doc_id = parent_doc_id

            if doc_id and expected_doc_id and doc_id != expected_doc_id:
                document_mismatches.append((nid, doc_id, pid, expected_doc_id))

        if missing_parents:
            errors.append(f"Phát hiện {len(missing_parents)} node có parent_id không tồn tại: {missing_parents[:5]}")
        if invalid_hierarchy:
            errors.append(f"Phát hiện {len(invalid_hierarchy)} vi phạm cấu trúc phân cấp pháp luật: {invalid_hierarchy[:5]}")
        if document_mismatches:
            errors.append(f"Phát hiện {len(document_mismatches)} node có document_id không khớp với parent: {document_mismatches[:5]}")

        # 1.3 Phát hiện chu trình (Cycle Detection) bằng thuật toán 3-color DFS (bất kỳ độ sâu nào)
        # 0: WHITE (unvisited), 1: GRAY (in current path), 2: BLACK (fully explored)
        color: Dict[str, int] = {nid: 0 for nid in node_map}
        cycles: List[List[str]] = []

        def dfs_cycle(curr_id: str, path: List[str]):
            color[curr_id] = 1
            parent = node_map[curr_id].get("parent_id")
            if parent and parent in node_map:
                if color[parent] == 1:
                    # Tìm thấy chu trình! Trích xuất chu trình
                    try:
                        idx = path.index(parent)
                        cycle_path = path[idx:] + [parent]
                    except ValueError:
                        cycle_path = [curr_id, parent]
                    cycles.append(cycle_path)
                elif color[parent] == 0:
                    dfs_cycle(parent, path + [parent])
            color[curr_id] = 2

        for nid in node_map:
            if color[nid] == 0:
                dfs_cycle(nid, [nid])

        if cycles:
            errors.append(f"Phát hiện {len(cycles)} chu trình bất thường trong quan hệ parent_id: {cycles[:3]}")

        # 1.4 Kiểm tra tính toàn vẹn của relations.json và đối chiếu với cây CONTAINS
        invalid_rel_endpoints: List[Tuple[str, str, str]] = []
        invalid_rel_types: List[Tuple[str, str]] = []
        duplicate_relations: List[Tuple[str, str, str]] = []
        self_loop_relations: List[str] = []
        rel_type_counts = Counter()

        seen_rel_triplets: Set[Tuple[str, str, str]] = set()
        contains_edges: Set[Tuple[str, str]] = set()

        for idx, r in enumerate(relations):
            sid = r.get("source_id") or r.get("from")
            tid = r.get("target_id") or r.get("to")
            rtype = r.get("type")

            if not sid or not tid or not rtype:
                errors.append(f"Relation tại vị trí {idx} thiếu source_id, target_id hoặc type.")
                continue

            triplet = (sid, rtype, tid)
            if triplet in seen_rel_triplets:
                duplicate_relations.append(triplet)
            seen_rel_triplets.add(triplet)

            if rtype not in ALLOWED_REL_TYPES:
                invalid_rel_types.append((f"{sid}->{tid}", rtype))
            else:
                rel_type_counts[rtype] += 1

            if sid == tid:
                self_loop_relations.append(sid)

            if sid not in node_map or tid not in node_map:
                invalid_rel_endpoints.append((sid, rtype, tid))
                continue

            if rtype == "CONTAINS":
                contains_edges.add((sid, tid))
                # Xác nhận node con không phải Document
                target_type = node_map[tid].get("type") or node_map[tid].get("label")
                if target_type == "Document":
                    errors.append(f"Cạnh CONTAINS bất hợp lệ: target {tid} là Document.")

                # Xác nhận parent_id của target khớp với source
                target_pid = node_map[tid].get("parent_id")
                if target_pid != sid:
                    errors.append(
                        f"Mâu thuẫn cạnh CONTAINS: ({sid})-[:CONTAINS]->({tid}) "
                        f"nhưng {tid} có parent_id là '{target_pid}'."
                    )

        if duplicate_relations:
            errors.append(f"Phát hiện {len(duplicate_relations)} quan hệ bị trùng lặp: {duplicate_relations[:5]}")
        if invalid_rel_endpoints:
            errors.append(f"Phát hiện {len(invalid_rel_endpoints)} relation có source hoặc target không tồn tại: {invalid_rel_endpoints[:5]}")
        if invalid_rel_types:
            errors.append(f"Phát hiện {len(invalid_rel_types)} relation có loại không hợp lệ: {invalid_rel_types[:5]}")
        if self_loop_relations:
            warnings.append(f"Phát hiện {len(self_loop_relations)} quan hệ tự trỏ chính nó: {self_loop_relations[:5]}")

        # 1.5 Đối chiếu 1-1 giữa parent_id của cây và quan hệ CONTAINS trong relations.json
        missing_contains_edges: List[Tuple[str, str]] = []
        for nid, n in node_map.items():
            ntype = n.get("type") or n.get("label")
            if ntype == "Document":
                continue
            pid = n.get("parent_id")
            if pid and pid in node_map:
                if (pid, nid) not in contains_edges:
                    missing_contains_edges.append((pid, nid))

        if missing_contains_edges:
            errors.append(
                f"Phát hiện {len(missing_contains_edges)} node có parent_id nhưng thiếu cạnh CONTAINS tương ứng trong relations: "
                f"{missing_contains_edges[:5]}"
            )

        status = "FAIL" if errors else ("WARN" if warnings else "PASS")

        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "statistics": {
                "total_nodes": len(nodes),
                "unique_node_ids": len(seen_ids),
                "total_relations": len(relations),
                "node_types": dict(type_counts),
                "relation_types": dict(rel_type_counts),
            },
        }

    # =========================================================================
    # 2. KIỂM TRA ĐỒNG BỘ RETRIEVAL ĐA TẦNG (RETRIEVAL SYNC CHECK)
    # =========================================================================
    def check_retrieval_sync(
        self,
        nodes_path: Optional[Path] = None,
        chroma_path: Optional[Path] = None,
        npz_path: Optional[Path] = None,
        check_neo4j: bool = True,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """Đối chiếu số lượng, danh sách ID và mã băm corpus giữa các backend retrieval.

        Args:
            nodes_path: Đường dẫn nodes.json.
            chroma_path: Đường dẫn ChromaDB directory.
            npz_path: Đường dẫn NPZ cache file.
            check_neo4j: Có kiểm tra Neo4j live hay không.
            strict: Nếu True, bất kỳ backend nào OFFLINE/UNKNOWN hoặc WARN sẽ chuyển thành FAIL.
        """
        n_path = Path(nodes_path) if nodes_path else self.data_dir / "nodes.json"
        c_path = Path(chroma_path) if chroma_path else self.chroma_path
        z_path = Path(npz_path) if npz_path else self.npz_path

        errors: List[str] = []
        warnings: List[str] = []
        sync_details: Dict[str, Any] = {}

        # 2.1 Lấy danh sách Article từ nodes.json
        if not n_path.exists():
            return {
                "status": "FAIL",
                "errors": [f"Không tìm thấy nodes.json: {n_path}"],
                "warnings": [],
                "sync_details": {},
            }

        with open(n_path, "r", encoding="utf-8") as f:
            all_nodes = json.load(f)

        node_map = {n["node_id"]: n for n in all_nodes if n.get("node_id")}
        json_articles = [
            n for n in all_nodes
            if (n.get("type") or n.get("label")) == "Article"
        ]
        json_article_ids = sorted([str(a["node_id"]) for a in json_articles])
        json_id_set = set(json_article_ids)

        expected_corpus_hash = compute_article_corpus_hash(json_articles, node_map)

        sync_details["nodes_json"] = {
            "article_count": len(json_article_ids),
            "expected_corpus_hash": expected_corpus_hash,
            "expected_model": self.expected_model_name,
            "expected_dimension": self.expected_dimension,
        }

        # 2.2 Kiểm tra NPZ Vector Cache
        npz_id_set = set()
        npz_hash = "UNKNOWN"
        npz_model = "UNKNOWN"
        npz_dim = "UNKNOWN"

        if z_path.exists():
            try:
                with np.load(z_path, allow_pickle=True) as data:
                    npz_ids = [str(x) for x in data["node_ids"]]
                    npz_id_set = set(npz_ids)
                    if "corpus_hash" in data:
                        npz_hash = str(data["corpus_hash"][0])
                    if "model_name" in data:
                        npz_model = str(data["model_name"][0])
                    if "dimension" in data:
                        npz_dim = int(data["dimension"][0])
                    elif "vectors" in data:
                        npz_dim = int(data["vectors"].shape[1])

                sync_details["npz_cache"] = {
                    "exists": True,
                    "article_count": len(npz_ids),
                    "corpus_hash": npz_hash,
                    "model_name": npz_model,
                    "dimension": npz_dim,
                }
            except Exception as e:
                msg = f"Không thể đọc file NPZ cache ({z_path.name}): {e}"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                sync_details["npz_cache"] = {"exists": True, "error": str(e)}
        else:
            msg = f"File NPZ cache không tồn tại: {z_path.name}"
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)
            sync_details["npz_cache"] = {"exists": False}

        # 2.3 Kiểm tra ChromaDB Collection (Chỉ đọc đúng collection 'legal_articles')
        chroma_id_set = set()
        chroma_hash = "UNKNOWN"
        chroma_model = "UNKNOWN"
        chroma_dim = "UNKNOWN"

        sqlite_db = c_path / "chroma.sqlite3"
        target_coll_name = self.target_chroma_collection

        if sqlite_db.exists():
            try:
                # Đọc qua SQLite uri read-only, có JOIN chặt chẽ theo collection_id
                conn = sqlite3.connect(f"file:{sqlite_db.resolve()}?mode=ro", uri=True)
                cur = conn.cursor()

                # 1. Tìm collection id chính xác
                cur.execute("SELECT id, dimension FROM collections WHERE name = ?", (target_coll_name,))
                coll_row = cur.fetchone()
                if not coll_row:
                    raise ValueError(f"Collection '{target_coll_name}' không tồn tại trong ChromaDB.")

                coll_id, coll_dim_col = coll_row[0], coll_row[1]

                # 2. Lấy metadata của đúng collection này
                cur.execute(
                    "SELECT key, str_value, int_value FROM collection_metadata WHERE collection_id = ?",
                    (coll_id,)
                )
                meta_dict = {}
                for k, s_val, i_val in cur.fetchall():
                    meta_dict[k] = s_val if s_val is not None else i_val

                chroma_hash = str(meta_dict.get("corpus_hash", "UNKNOWN"))
                chroma_model = str(meta_dict.get("embedding_model", "UNKNOWN"))
                chroma_dim = meta_dict.get("dimension") or coll_dim_col or "UNKNOWN"
                if chroma_dim != "UNKNOWN":
                    chroma_dim = int(chroma_dim)

                # 3. Lấy đúng danh sách embedding_id thuộc về collection này
                cur.execute("""
                    SELECT DISTINCT e.embedding_id
                    FROM embeddings e
                    JOIN segments s ON e.segment_id = s.id
                    WHERE s.collection = ?
                """, (coll_id,))
                chroma_ids = [r[0] for r in cur.fetchall()]
                chroma_id_set = set(chroma_ids)
                conn.close()

                sync_details["chroma_db"] = {
                    "exists": True,
                    "collection": target_coll_name,
                    "article_count": len(chroma_ids),
                    "corpus_hash": chroma_hash,
                    "model_name": chroma_model,
                    "dimension": chroma_dim,
                }
            except Exception as se:
                msg = f"Lỗi đọc ChromaDB sqlite ({c_path.name}): {se}"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                sync_details["chroma_db"] = {"exists": True, "error": str(se)}
        elif c_path.exists():
            # Thử qua chromadb PersistentClient
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(c_path))
                coll = client.get_collection(target_coll_name)
                coll_data = coll.get(include=[])
                chroma_ids = coll_data.get("ids", [])
                chroma_id_set = set(chroma_ids)
                meta = coll.metadata or {}
                chroma_hash = str(meta.get("corpus_hash", "UNKNOWN"))
                chroma_model = str(meta.get("embedding_model", "UNKNOWN"))
                chroma_dim = meta.get("dimension", "UNKNOWN")
                sync_details["chroma_db"] = {
                    "exists": True,
                    "collection": target_coll_name,
                    "article_count": len(chroma_ids),
                    "corpus_hash": chroma_hash,
                    "model_name": chroma_model,
                    "dimension": chroma_dim,
                }
            except Exception as ce:
                msg = f"Không thể mở ChromaDB collection '{target_coll_name}': {ce}"
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                sync_details["chroma_db"] = {"exists": True, "error": str(ce)}
        else:
            msg = f"Thư mục ChromaDB không tồn tại: {c_path}"
            if strict:
                errors.append(msg)
            else:
                warnings.append(msg)
            sync_details["chroma_db"] = {"exists": False}

        # 2.4 Kiểm tra Neo4j (nếu yêu cầu)
        neo4j_id_set = set()
        if check_neo4j:
            try:
                from src.graph.neo4j_client import Neo4jClient

                neo_client = Neo4jClient()
                rows = neo_client.execute_read("MATCH (n:Article) RETURN n.node_id AS node_id")
                neo4j_ids = [str(r["node_id"]) for r in rows if r.get("node_id")]
                neo4j_id_set = set(neo4j_ids)
                sync_details["neo4j"] = {
                    "online": True,
                    "article_count": len(neo4j_ids),
                }
            except Exception as e:
                sync_details["neo4j"] = {
                    "online": False,
                    "message": f"Neo4j offline ({e}).",
                }
                msg = f"Neo4j hiện đang offline ({e})."
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

        # 2.5 Đối chiếu tính đồng bộ Article IDs
        if npz_id_set:
            missing_in_npz = json_id_set - npz_id_set
            extra_in_npz = npz_id_set - json_id_set
            if missing_in_npz or extra_in_npz:
                errors.append(
                    f"Lệch Article IDs giữa nodes.json và NPZ: "
                    f"nodes.json có {len(missing_in_npz)} node thiếu trong NPZ; "
                    f"NPZ có {len(extra_in_npz)} node thừa."
                )
        elif self.active_vector_backend == "npz" or strict:
            errors.append("NPZ cache không có dữ liệu Article IDs hoặc không tồn tại.")

        if chroma_id_set:
            missing_in_chroma = json_id_set - chroma_id_set
            extra_in_chroma = chroma_id_set - json_id_set
            if missing_in_chroma or extra_in_chroma:
                errors.append(
                    f"Lệch Article IDs giữa nodes.json và ChromaDB: "
                    f"nodes.json có {len(missing_in_chroma)} node thiếu trong Chroma; "
                    f"Chroma có {len(extra_in_chroma)} node thừa."
                )
        elif self.active_vector_backend == "chroma" and strict:
            errors.append(f"ChromaDB collection '{target_coll_name}' không có dữ liệu Article IDs.")

        if neo4j_id_set:
            missing_in_neo = json_id_set - neo4j_id_set
            extra_in_neo = neo4j_id_set - json_id_set
            if missing_in_neo or extra_in_neo:
                errors.append(
                    f"Lệch Article IDs giữa nodes.json và Neo4j: "
                    f"nodes.json có {len(missing_in_neo)} node thiếu trong Neo4j; "
                    f"Neo4j có {len(extra_in_neo)} node thừa."
                )

        # 2.6 Kiểm tra Stale Index qua Corpus Hash
        if npz_hash != "UNKNOWN" and npz_hash != expected_corpus_hash:
            errors.append(
                f"STALE EMBEDDING INDEX trong NPZ: Corpus hash trong NPZ ({npz_hash[:12]}...) "
                f"không khớp với nội dung hiện tại của nodes.json ({expected_corpus_hash[:12]}...). "
                f"BM25 đang dùng dữ liệu mới nhưng Semantic đang dùng index cũ!"
            )

        if chroma_hash != "UNKNOWN" and chroma_hash != expected_corpus_hash:
            errors.append(
                f"STALE EMBEDDING INDEX trong ChromaDB: Corpus hash trong Chroma ({chroma_hash[:12]}...) "
                f"không khớp với nội dung hiện tại của nodes.json ({expected_corpus_hash[:12]}...). "
                f"Cần chạy lại scripts/embed_nodes.py."
            )

        # 2.7 Kiểm tra Model & Dimension
        if npz_dim not in ("UNKNOWN", self.expected_dimension):
            errors.append(f"NPZ dimension sai lệch: {npz_dim} (kỳ vọng {self.expected_dimension}).")
        if chroma_dim not in ("UNKNOWN", self.expected_dimension):
            errors.append(f"Chroma dimension sai lệch: {chroma_dim} (kỳ vọng {self.expected_dimension}).")

        status = "FAIL" if errors else ("WARN" if warnings else "PASS")

        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "sync_details": sync_details,
        }

    # =========================================================================
    # 3. KIỂM TRA LIÊN KẾT CHÉO KHI MỞ RỘNG VĂN BẢN (RESOLVABLE REFERENCES)
    # =========================================================================
    def check_resolvable_references(
        self,
        nodes_path: Optional[Path] = None,
        existing_doc_ids: Optional[Set[str]] = None,
        candidate_doc_ids: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Rà soát các dẫn chiếu chưa giải quyết (unresolved) và đề xuất quan hệ khi thêm văn bản mới.
        Chỉ đánh dấu RESOLVABLE khi CẢ SOURCE VÀ TARGET ENDPOINT ĐỀU TỒN TẠI THẬT SỰ.
        Nếu chỉ có một bên hoặc chỉ khớp từ khóa, xếp loại CANDIDATE_REVIEW, không tự kích hoạt cạnh.
        """
        candidate_doc_ids = set(candidate_doc_ids or [])
        existing_ids = set(existing_doc_ids or [])

        n_path = Path(nodes_path) if nodes_path else self.data_dir / "nodes.json"
        node_map = {}
        if n_path.exists():
            with open(n_path, "r", encoding="utf-8") as f:
                nodes = json.load(f)
            for n in nodes:
                nid = n.get("node_id")
                if nid:
                    node_map[nid] = n
                if (n.get("type") or n.get("label")) == "Document":
                    did = n.get("document_id") or n.get("node_id")
                    if did:
                        existing_ids.add(str(did))

        all_target_doc_ids = existing_ids.union(candidate_doc_ids)

        unres_refs = []
        if self.unres_refs_path.exists():
            with open(self.unres_refs_path, "r", encoding="utf-8") as f:
                unres_refs = json.load(f)

        unres_docs = []
        if self.unres_docs_path.exists():
            with open(self.unres_docs_path, "r", encoding="utf-8") as f:
                unres_docs = json.load(f)

        resolvable_doc_relations: List[Dict[str, Any]] = []
        candidate_review_doc_relations: List[Dict[str, Any]] = []
        unresolved_doc_remaining: List[Dict[str, Any]] = []

        doc_keyword_mapping = {
            "33/2005/qh11": "BLDS_2005",
            "bộ luật dân sự 2005": "BLDS_2005",
            "bộ luật dân sự năm 2005": "BLDS_2005",
            "163/2006/nđ-cp": "ND_163_2006",
            "11/2012/nđ-cp": "ND_11_2012",
            "144/2006/nđ-cp": "ND_144_2006",
            "03/2006/nq-hđtp": "NQ_03_2006",
            "luật nhà ở 2014": "LUAT_NHA_O_2014",
            "luật nhà ở năm 2014": "LUAT_NHA_O_2014",
            "luật giao thông đường bộ 2008": "LUAT_GTDB_2008",
            "luật giao thông đường bộ năm 2008": "LUAT_GTDB_2008",
            "luật giao thông đường bộ": "LUAT_GTDB_2008",
            "luật nhà ở": "LUAT_NHA_O_2014",
            "203/2025/qh15": "NQ_203_2025",
        }

        # 3.1 Kiểm tra unresolved_document_relations
        for item in unres_docs:
            target_id = item.get("target_id")
            source_id = item.get("source_id")
            rel_type = item.get("type")
            so_hieu = str(item.get("target_so_hieu") or "").lower()
            name = str(item.get("target_name") or "").lower()

            # Xác định target doc
            resolved_target_doc = None
            if target_id and target_id in all_target_doc_ids:
                resolved_target_doc = target_id
            else:
                for kw, mapped_id in doc_keyword_mapping.items():
                    if kw in so_hieu or kw in name:
                        if mapped_id in all_target_doc_ids:
                            resolved_target_doc = mapped_id
                            break

            source_exists = source_id and (source_id in all_target_doc_ids or source_id in node_map)

            # Chỉ RESOLVABLE khi CẢ SOURCE VÀ TARGET ĐỀU XÁC ĐỊNH VÀ TỒN TẠI
            if source_exists and resolved_target_doc:
                resolvable_doc_relations.append({
                    "source_id": source_id,
                    "relation_type": rel_type,
                    "target_id": resolved_target_doc,
                    "evidence": item.get("evidence"),
                    "action": f"KÍCH HOẠT QUAN HỆ ':{rel_type}' GIỮA {source_id} VÀ {resolved_target_doc}",
                })
            elif source_exists or resolved_target_doc:
                candidate_review_doc_relations.append({
                    "source_id": source_id,
                    "relation_type": rel_type,
                    "target_id": resolved_target_doc or target_id,
                    "reason": "Chỉ có 1 đầu endpoint tồn tại; cần văn bản bổ sung để kích hoạt cạnh.",
                    "evidence": item.get("evidence"),
                })
            else:
                unresolved_doc_remaining.append(item)

        # 3.2 Kiểm tra unresolved_references (dẫn chiếu điều khoản Article)
        resolvable_article_refs: List[Dict[str, Any]] = []
        candidate_review_article_refs: List[Dict[str, Any]] = []
        unresolved_article_remaining: List[Dict[str, Any]] = []

        for item in unres_refs:
            src = item.get("source_id")
            evidence = str(item.get("evidence") or "").lower()
            citation = item.get("citation")

            matched_doc = None
            for kw, mapped_id in doc_keyword_mapping.items():
                if kw in evidence:
                    if mapped_id in all_target_doc_ids:
                        matched_doc = mapped_id
                        break

            # Kiểm tra xem source có tồn tại không
            source_exists = src in node_map if node_map else True

            # Kiểm tra xem target article node có thực sự tồn tại trong đồ thị chưa
            # Ví dụ: LUAT_NHA_O_2014_D12
            target_article_id = None
            if matched_doc and citation:
                import re
                d_match = re.search(r"điều\s+(\d+)", citation, re.IGNORECASE)
                if d_match:
                    target_article_id = f"{matched_doc}_D{d_match.group(1)}"

            if source_exists and target_article_id and target_article_id in node_map:
                resolvable_article_refs.append({
                    "source_id": src,
                    "citation": citation,
                    "target_node_id": target_article_id,
                    "evidence": item.get("evidence"),
                    "resolved_by_document": matched_doc,
                    "action": f"KÍCH HOẠT DẪN CHIẾU ':REFERENCES' TỪ {src} TỚI {target_article_id}",
                })
            elif matched_doc:
                # Đã khớp văn bản nhưng chưa có node Điều cụ thể trong đồ thị
                candidate_review_article_refs.append({
                    "source_id": src,
                    "citation": citation,
                    "target_document": matched_doc,
                    "reason": f"Khớp văn bản {matched_doc} nhưng node Điều tương ứng ({target_article_id or 'chưa rõ'}) chưa có trong đồ thị.",
                    "evidence": item.get("evidence"),
                })
            else:
                unresolved_article_remaining.append(item)

        return {
            "total_unresolved_doc_relations": len(unres_docs),
            "resolvable_doc_relations": resolvable_doc_relations,
            "candidate_review_doc_relations": candidate_review_doc_relations,
            "remaining_unresolved_doc_relations": len(unresolved_doc_remaining),
            "total_unresolved_article_references": len(unres_refs),
            "resolvable_article_references": resolvable_article_refs,
            "candidate_review_article_references": candidate_review_article_refs,
            "remaining_unresolved_article_references": len(unresolved_article_remaining),
        }

    # =========================================================================
    # 4. TỔNG HỢP VÀ XUẤT BÁO CÁO (REPORT EXPORT)
    # =========================================================================
    def generate_full_report(
        self,
        nodes_path: Optional[Path] = None,
        relations_path: Optional[Path] = None,
        candidate_doc_ids: Optional[List[str]] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """Chạy toàn bộ 3 bước kiểm tra và sinh báo cáo tổng thể."""
        val_res = self.validate_graph_data(nodes_path, relations_path)
        sync_res = self.check_retrieval_sync(nodes_path, strict=strict)
        ref_res = self.check_resolvable_references(
            nodes_path=nodes_path,
            candidate_doc_ids=set(candidate_doc_ids or [])
        )

        overall_status = "PASS"
        if val_res["status"] == "FAIL" or sync_res["status"] == "FAIL":
            overall_status = "FAIL"
        elif val_res["status"] == "WARN" or sync_res["status"] == "WARN":
            overall_status = "FAIL" if strict else "WARN"

        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "overall_status": overall_status,
            "strict_mode": strict,
            "validation": val_res,
            "retrieval_synchronization": sync_res,
            "unresolved_references_analysis": ref_res,
            "recommended_actions": self._build_recommended_actions(val_res, sync_res, ref_res),
        }
        return report

    def _build_recommended_actions(
        self,
        val_res: Dict[str, Any],
        sync_res: Dict[str, Any],
        ref_res: Dict[str, Any],
    ) -> List[str]:
        actions = []
        if val_res["errors"]:
            actions.append("SỬA LỖI DỮ LIỆU ĐỒ THỊ: Khắc phục duplicate IDs, parent_id thiếu hoặc chu trình trước khi nạp Neo4j.")
        if sync_res["errors"]:
            actions.append("ĐỒNG BỘ LẠI VECTOR EMBEDDING: Chạy 'python scripts/embed_nodes.py --store dual' để đồng bộ ChromaDB và NPZ với nodes.json.")
        if ref_res["resolvable_doc_relations"] or ref_res["resolvable_article_references"]:
            actions.append(
                f"KÍCH HOẠT LIÊN KẾT CHÉO: Có {len(ref_res['resolvable_doc_relations'])} quan hệ văn bản và "
                f"{len(ref_res['resolvable_article_references'])} dẫn chiếu đã đủ 2 đầu endpoint, có thể chuyển thành cạnh trong KG."
            )
        if not actions:
            actions.append("Hệ thống đạt chuẩn đồng bộ 100%. Sẵn sàng mở rộng văn bản mới an toàn.")
        return actions

    def export_markdown_report(self, report_data: Dict[str, Any], output_path: Path) -> Path:
        """Xuất báo cáo định dạng Markdown trực quan."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Báo Cáo Kiểm Định & Đồng Bộ Knowledge Graph",
            "",
            f"- **Thời gian kiểm tra:** {report_data['timestamp']}",
            f"- **Trạng thái tổng thể:** **{report_data['overall_status']}** (Strict Mode: `{report_data.get('strict_mode', False)}`)",
            "",
            "## 1. Kết Quả Kiểm Định Dữ Liệu Đồ Thị (Graph Validation)",
            "",
        ]

        val = report_data["validation"]
        stats = val.get("statistics", {})
        lines.append(f"- **Trạng thái:** `{val['status']}`")
        lines.append(f"- **Tổng số node:** {stats.get('total_nodes', 0):,}")
        lines.append(f"- **Tổng số quan hệ:** {stats.get('total_relations', 0):,}")
        lines.append(f"- **Phân bố loại node:** `{stats.get('node_types', {})}`")
        lines.append(f"- **Phân bố loại quan hệ:** `{stats.get('relation_types', {})}`")

        if val["errors"]:
            lines.append("\n### ❌ Lỗi Phát Hiện:")
            for err in val["errors"]:
                lines.append(f"- {err}")

        if val["warnings"]:
            lines.append("\n### ⚠️ Cảnh Báo:")
            for w in val["warnings"]:
                lines.append(f"- {w}")

        lines.extend([
            "",
            "## 2. Kết Quả Đối Soát Đồng Bộ Retrieval Đa Tầng",
            "",
        ])

        sync = report_data["retrieval_synchronization"]
        lines.append(f"- **Trạng thái:** `{sync['status']}`")
        details = sync.get("sync_details", {})

        lines.append("\n| Kho lưu trữ | Số lượng Article | Corpus Hash SHA256 | Model | Dimension |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")

        nj = details.get("nodes_json", {})
        lines.append(f"| nodes.json | {nj.get('article_count', 'N/A')} | `{str(nj.get('expected_corpus_hash', 'N/A'))[:12]}...` | - | - |")

        npz = details.get("npz_cache", {})
        if npz.get("exists"):
            lines.append(f"| NPZ Cache | {npz.get('article_count', 'N/A')} | `{str(npz.get('corpus_hash', 'N/A'))[:12]}...` | {npz.get('model_name', 'N/A')} | {npz.get('dimension', 'N/A')} |")
        else:
            lines.append("| NPZ Cache | KHÔNG TỒN TẠI | - | - | - |")

        ch = details.get("chroma_db", {})
        if ch.get("exists") and "article_count" in ch:
            lines.append(f"| ChromaDB | {ch.get('article_count', 'N/A')} | `{str(ch.get('corpus_hash', 'N/A'))[:12]}...` | {ch.get('model_name', 'N/A')} | {ch.get('dimension', 'N/A')} |")
        else:
            lines.append(f"| ChromaDB | OFFLINE / LỖI | - | - | - |")

        neo = details.get("neo4j", {})
        if neo.get("online"):
            lines.append(f"| Neo4j (ONLINE) | {neo.get('article_count', 0)} | (Live Graph) | - | - |")
        else:
            lines.append(f"| Neo4j | OFFLINE | - | - | - |")

        if sync["errors"]:
            lines.append("\n### ❌ Lỗi Mất Đồng Bộ Retrieval:")
            for err in sync["errors"]:
                lines.append(f"- {err}")

        lines.extend([
            "",
            "## 3. Phân Tích Liên Kết Chéo & Dẫn Chiếu Treo",
            "",
        ])
        ref = report_data["unresolved_references_analysis"]
        lines.append(f"- **Tổng số quan hệ văn bản chưa giải quyết:** {ref.get('total_unresolved_doc_relations', 0)}")
        lines.append(f"- **Tổng số dẫn chiếu điều luật chưa giải quyết:** {ref.get('total_unresolved_article_references', 0)}")

        if ref.get("resolvable_doc_relations"):
            lines.append("\n### 🔗 Quan Hệ Văn Bản Đủ Điều Kiện Kích Hoạt (2 Đầu Endpoint Hợp Lệ):")
            for r in ref["resolvable_doc_relations"]:
                lines.append(f"- **{r['source_id']}** --`:{r['relation_type']}`--> **{r['target_id']}** (Căn cứ: *{r.get('evidence', '')[:100]}...*)")

        if ref.get("candidate_review_doc_relations"):
            lines.append("\n### 🔍 Quan Hệ Cần Rà Soát (Chỉ có 1 đầu Endpoint hoặc cần thêm văn bản):")
            for r in ref["candidate_review_doc_relations"]:
                lines.append(f"- **{r['source_id']}** --`:{r['relation_type']}`--> **{r['target_id']}** ({r.get('reason')})")

        if ref.get("resolvable_article_references"):
            lines.append("\n### 🔗 Dẫn Chiếu Điều Luật Đủ Điều Kiện Kích Hoạt:")
            for r in ref["resolvable_article_references"]:
                lines.append(f"- **{r['source_id']}** dẫn chiếu *{r['citation']}* tới node **{r['target_node_id']}**")

        if ref.get("candidate_review_article_refs"):
            lines.append("\n### 🔍 Dẫn Chiếu Điều Luật Chờ Bổ Sung Node Điều:")
            for r in ref["candidate_review_article_refs"]:
                lines.append(f"- **{r['source_id']}** ({r['citation']}): {r['reason']}")

        lines.extend([
            "",
            "## 4. Hành Động Khuyến Nghị Tiếp Theo",
            "",
        ])
        for act in report_data.get("recommended_actions", []):
            lines.append(f"- {act}")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
