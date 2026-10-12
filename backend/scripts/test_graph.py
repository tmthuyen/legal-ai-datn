
import gc

from src.graph.builder_graph import BuilderGraph
from src.graph.graph_repository import LegalGraphRepository
from src.graph.graph_service import LegalGraphService
from src.graph.neo4j_client import Neo4jClient
from src.utils.logger import setup_logger


class TestGraph:
    def __init__(self, service: LegalGraphService):
        self.logger = setup_logger(name="test_venv", filename="test_venv.log")
        self.logger.info("TestVenv initialized.")
        self.builder_graph = BuilderGraph()
        self.legal_service = service

    def test_import(self):
        self.logger.info("Ok import of modules...")
        self.builder_graph.add_node("node1", {"data": "value1"})
        
    def test_graph(self):
        self.logger.info("Testing graph service...")
        
        # nodes
        legal_nodes = self.legal_service.get_all_legal_nodes(limit=5000)
        self.logger.info(f"Retrieved {len(legal_nodes)} legal nodes.")
        
        # 10 first nodes
        for i, node in enumerate(legal_nodes[:10]):
            self.logger.info(f"Node {i+1}: {node}")
        
        # relationships
        legal_relationships = self.legal_service.get_all_legal_relationships(limit=5000)
        self.logger.info(f"Retrieved {len(legal_relationships)} legal relationships.")
        
        # 10 first relationships
        for i, relationship in enumerate(legal_relationships[:10]):
            self.logger.info(f"Relationship {i+1}: {relationship}")
        
        gc.collect()  # Force garbage collection to free up memory
        
        
        

neo4j_client = Neo4jClient()
repo = LegalGraphRepository(db=neo4j_client)
service = LegalGraphService(repository=repo)
test_graph = TestGraph(service=service)
test_graph.test_import()
# test_graph.test_graph()

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

tokenizer = AutoTokenizer.from_pretrained("tmtdev/vietnam-law-llama3")
model = AutoModelForCausalLM.from_pretrained(
    "tmtdev/vietnam-law-llama3",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Test
question = "Tuổi kết hôn tối thiểu ở Việt Nam?"
prompt = f"Hỏi: {question}\nĐáp: "
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.3)
answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(answer)
