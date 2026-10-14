"""
neo4j_client.py
Quản lý kết nối tới Neo4j Graph Database.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session

from src.common.custom_exception import CustomException

load_dotenv()
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Wrapper cho kết nối và truy vấn Neo4j."""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        if not self.password:
            raise CustomException(
                message="Mật khẩu Neo4j không được cung cấp.",
                status_code=500
            )
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver: Optional[Driver] = None

        # Kiểm tra kết nối ngay khi khởi tạo
        if not self.verify_connectivity():
            raise CustomException(
                message="Không thể kết nối tới Neo4j.",
                status_code=500
            )
            
        # successful connection log
        logger.info(f"Kết nối thành công tới Neo4j tại {self.uri} với database '{self.database}'.")

    def connect(self) -> Driver:
        """Khởi tạo hoặc trả về Driver kết nối tới Neo4j."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
        return self._driver

    @property
    def driver(self) -> Driver:
        """Thuộc tính truy cập Driver kết nối."""
        return self.connect()

    def verify_connectivity(self) -> bool:
        """Kiểm tra tính khả dụng của kết nối tới Neo4j."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Lỗi kiểm tra kết nối Neo4j ({self.uri}): {e}")
            return False

    def close(self) -> None:
        """Đóng kết nối Driver Neo4j."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def session(self) -> Session:
        """Tạo một phiên làm việc (Session) mới với database đã cấu hình."""
        return self.driver.session(database=self.database)

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Thực thi câu truy vấn đọc (READ) Cypher và trả về danh sách kết quả dạng dict."""
        with self.session() as s:
            result = s.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Thực thi câu truy vấn ghi (WRITE) Cypher và trả về danh sách kết quả dạng dict."""
        with self.session() as s:
            result = s.run(query, parameters or {})
            return [record.data() for record in result]

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
