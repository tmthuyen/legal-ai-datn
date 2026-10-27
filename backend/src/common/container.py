"""
container.py
Composition root: khởi tạo và giữ các service dùng chung cho toàn tiến trình.

Mục đích:
- Gom một chỗ duy nhất việc wiring service (Neo4j, graph, embedding, semantic, model, retrieval)
  để API và script tái sử dụng, tránh lặp cấu hình ở từng client.
- `build_services` nạp model ngay khi được gọi (model nạp một lần, dùng cho mọi request).
"""

from dataclasses import dataclass
from typing import Optional

from src.common.setting_config import Settings, get_settings
from src.graph.embedder import NodeEmbedder
from src.graph.graph_repository import LegalGraphRepository
from src.graph.graph_service import LegalGraphService
from src.graph.neo4j_client import Neo4jClient
from src.models.legal_model import LegalReasoningModel
from src.retrieval.hybrid import BM25Searcher, HybridSearcher
from src.retrieval.legal_query_extractor import LegalQueryExtractor
from src.retrieval.retrieval_service import RetrievalService
from src.retrieval.semantic import SemanticSearcher
from src.utils.logger import setup_logger

logger = setup_logger("container", "container.log")


def build_embedding_pipeline(args):
    """Wiring pipeline embedding; chế độ Chroma không cần kết nối Neo4j."""
    from src.vector.chroma_store import ChromaVectorStore
    from src.vector.embedding_pipeline import run_embedding_pipeline

    settings = get_settings()
    client = None
    if args.store in ("neo4j", "dual") and not args.dry_run:
        client = Neo4jClient(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
    embedder = NodeEmbedder(batch_size=args.batch_size)

    def store_factory(model_name, dimension):
        """Tạo persistent store theo cấu hình chung."""
        return ChromaVectorStore(
            settings.chroma_path, settings.chroma_collection, model_name, dimension
        )

    return run_embedding_pipeline, client, embedder, store_factory


@dataclass
class AppServices:
    """Tập hợp service dùng chung, khởi tạo một lần và tái sử dụng cho mọi request.

    Attributes:
        settings: Cấu hình ứng dụng đã dùng để khởi tạo service.
        neo4j_client: Client kết nối Neo4j.
        graph_repository: Repository truy vấn đồ thị.
        graph_service: Service nghiệp vụ trên đồ thị.
        embedder: Bộ sinh embedding cho query/passage.
        semantic_service: Service tìm kiếm ngữ nghĩa trên vector index.
        legal_model: Mô hình suy luận pháp luật đã fine-tune.
        query_extractor: Bộ trích xuất phân cấp luật từ câu hỏi.
        retrieval_service: Orchestrator pipeline Retrieval V1.
    """

    settings: Settings
    neo4j_client: Neo4jClient
    graph_repository: LegalGraphRepository
    graph_service: LegalGraphService
    embedder: NodeEmbedder
    semantic_service: SemanticSearcher
    legal_model: LegalReasoningModel
    query_extractor: LegalQueryExtractor
    retrieval_service: RetrievalService
    vector_store: object = None
    bm25_service: Optional[BM25Searcher] = None
    hybrid_service: Optional[HybridSearcher] = None

    def close(self) -> None:
        """Giải phóng tài nguyên dùng chung (đóng kết nối Neo4j)."""
        logger.info("Đóng tài nguyên service dùng chung.")
        self.neo4j_client.close()
        if self.vector_store is not None:
            self.vector_store.close()


def build_services(settings: Optional[Settings] = None) -> AppServices:
    """Khởi tạo toàn bộ service dùng chung dựa trên cấu hình.

    Hàm nạp sẵn embedding model vào bộ nhớ; mô hình suy luận được nạp ngay trong
    constructor của `LegalReasoningModel`.

    Args:
        settings: Cấu hình ứng dụng. Nếu None, lấy từ `get_settings()`.

    Returns:
        AppServices đã sẵn sàng sử dụng.
    """
    settings = settings or get_settings()

    logger.info("Khởi tạo Neo4j client (%s).", settings.neo4j_uri)
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )

    graph_repository = LegalGraphRepository(db=neo4j_client)
    graph_service = LegalGraphService(repository=graph_repository)

    logger.info("Nạp embedding model: %s", settings.embedding_model_name)
    embedder = NodeEmbedder(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
        batch_size=settings.embedding_batch_size,
    )
    embedder.load_model()
    vector_store = None
    if settings.vector_backend == "chroma":
        from src.vector.chroma_store import ChromaVectorStore

        vector_store = ChromaVectorStore(
            settings.chroma_path,
            settings.chroma_collection,
            embedder.model_name,
            embedder.dimension,
            create=False,
        )
        if not vector_store.count():
            vector_store.close()
            neo4j_client.close()
            raise ValueError("Chroma collection chưa được populate.")
    semantic_service = SemanticSearcher(
        neo4j_client=neo4j_client, embedder=embedder, vector_store=vector_store
    )

    logger.info("Khởi tạo BM25 lexical searcher...")
    bm25_service = BM25Searcher(neo4j_client=neo4j_client)

    logger.info("Khởi tạo Hybrid searcher (Semantic + BM25 với RRF)...")
    hybrid_service = HybridSearcher(
        semantic_searcher=semantic_service,
        bm25_searcher=bm25_service,
    )

    logger.info("Nạp reasoning model: %s", settings.hf_model_id)
    legal_model = LegalReasoningModel(
        base_model_name=settings.hf_base_model,
        model_id=settings.hf_model_id,
        revision=settings.hf_revision,
    )
    query_extractor = LegalQueryExtractor(legal_model=legal_model)

    retrieval_service = RetrievalService(
        legal_graph_service=graph_service,
        legal_query_extractor=query_extractor,
        semantic_service=semantic_service,
        hybrid_service=hybrid_service,
    )

    logger.info("Khởi tạo service dùng chung hoàn tất.")

    return AppServices(
        settings=settings,
        neo4j_client=neo4j_client,
        graph_repository=graph_repository,
        graph_service=graph_service,
        embedder=embedder,
        semantic_service=semantic_service,
        legal_model=legal_model,
        query_extractor=query_extractor,
        retrieval_service=retrieval_service,
        vector_store=vector_store,
        bm25_service=bm25_service,
        hybrid_service=hybrid_service,
    )
