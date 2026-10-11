
from src.graph.builder_graph import BuilderGraph
from src.utils.logger import setup_logger


class TestVenv:
    def __init__(self):
        self.logger = setup_logger(name="test_venv", filename="test_venv.log")
        self.logger.info("TestVenv initialized.")
        self.builder_graph = BuilderGraph()
        
    def test_import(self):
        self.logger.info("Ok import of modules...")
        self.builder_graph.add_node("node1", {"data": "value1"})
        
test_venv = TestVenv()
test_venv.test_import()