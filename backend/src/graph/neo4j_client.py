"""
neo4j_client.py
Quản lý kết nối tới Neo4j Graph Database.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, Session

load_dotenv()
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Wrapper cho kết nối và truy vấn Neo4j."""

    def __init__(
<<<<<<< HEAD:backend/src/graph/neo4j_client.py
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
            raise ValueError(
                "NEO4J_PASSWORD chưa được cấu hình. "
                "Vui lòng thiết lập biến NEO4J_PASSWORD trong file .env hoặc truyền vào khi khởi tạo Neo4jClient."
=======
            self,
            uri: str = setting.neo4j_uri,
            username: str = setting.neo4j_username,
            password: str = setting.neo4j_password,
            database: str = setting.neo4j_database,
        ):
        self._driver: Driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
        )
        self._database = database
        

    def verify_connection(self) -> None:
        self._driver.verify_connectivity()

    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        with self._driver.session(
            database=self._database
        ) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        with self._driver.session(
            database=self._database
        ) as session:
            return session.execute_write(
                self._run_write,
                query,
                parameters or {},
>>>>>>> a48714f (fea: retrieval):backend/src/graph/neo4j_client_1.py
            )
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver: Optional[Driver] = None

    def connect(self) -> Driver:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
        return self._driver

    @property
    def driver(self) -> Driver:
        return self.connect()

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def session(self) -> Session:
        return self.driver.session(database=self.database)

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self.session() as s:
            result = s.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self.session() as s:
            result = s.run(query, parameters or {})
            return [record.data() for record in result]

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# OLD CODE (THUYÊN)

from typing import Any

from neo4j import GraphDatabase, Driver

from src.common.setting_config import Settings, get_settings

setting: Settings = get_settings()
class Neo4jClient_1:
    def __init__(
        self,
        ):
        self._driver: Driver = GraphDatabase.driver(
            setting.neo4j_uri,
            auth=(setting.neo4j_username, setting.neo4j_password),
        )
        self._database = setting.neo4j_database
        

    def verify_connection(self) -> None:
        self._driver.verify_connectivity()

    def execute_read(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        with self._driver.session(
            database=self._database
        ) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        with self._driver.session(
            database=self._database
        ) as session:
            return session.execute_write(
                self._run_write,
                query,
                parameters or {},
            )

    @staticmethod
    def _run_write(
        tx,
        query: str,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result = tx.run(query, parameters)
        return [record.data() for record in result]

    def close(self) -> None:
        self._driver.close()