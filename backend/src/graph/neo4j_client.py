
from typing import Any

from neo4j import GraphDatabase, Driver

from src.common.setting_config import Settings, get_settings

setting: Settings = get_settings()
class Neo4jClient:
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