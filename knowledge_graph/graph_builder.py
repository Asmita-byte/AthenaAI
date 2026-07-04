import json
import pickle
from pathlib import Path

import networkx as nx

from backend.config import get_settings
from backend.core.logging import get_logger
from knowledge_graph.entity_extractor import EntityExtractor

settings = get_settings()
logger = get_logger(__name__)


class GraphBuilder:

    def __init__(self):
        self.graph = nx.Graph()
        self.entity_extractor = EntityExtractor()

    def add_document(self, document_id: str, chunks: list[dict]) -> None:
        self.graph.add_node(document_id, node_type="document")

        for chunk in chunks:
            content = chunk.get("content", "")
            chunk_id = chunk.get("id", "")

            self.graph.add_node(chunk_id, node_type="chunk", document_id=document_id)
            self.graph.add_edge(document_id, chunk_id, relation="contains")

            entities = self.entity_extractor.extract(content)

            for entity_type, values in entities.items():
                for value in values:
                    entity_node = f"{entity_type}:{value}"
                    self.graph.add_node(entity_node, node_type=entity_type, value=value)
                    self.graph.add_edge(chunk_id, entity_node, relation="mentions")

        logger.info(
            "Document added to graph",
            document_id=document_id,
            nodes=self.graph.number_of_nodes(),
            edges=self.graph.number_of_edges(),
        )

    def save(self, document_id: str) -> str:
        graph_path = settings.storage_graphs_dir / f"{document_id}_graph.pkl"
        with open(graph_path, "wb") as f:
            pickle.dump(self.graph, f)
        logger.info("Graph saved", path=str(graph_path))
        return str(graph_path)

    def load(self, document_id: str) -> bool:
        graph_path = settings.storage_graphs_dir / f"{document_id}_graph.pkl"
        if not graph_path.exists():
            return False
        with open(graph_path, "rb") as f:
            self.graph = pickle.load(f)
        return True

    def get_stats(self) -> dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
        }
