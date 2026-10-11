
 


from src.utils.logger import setup_logger
logger = setup_logger(name='builder_graph', filename='builder_graph.log')  

class BuilderGraph:
    def __init__(self):
        self.graph = {} 
        
        logger.info("BuilderGraph initialized.")
        
    def add_node(self, node_id: str, node_data: dict):
        self.graph[node_id] = node_data
        logger.info(f"Node {node_id} added to the graph.")
    