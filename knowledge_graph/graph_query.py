from backend.core.logging import get_logger
from knowledge_graph.graph_builder import GraphBuilder

logger = get_logger(__name__)


class GraphQuery:

    def __init__(self, builder: GraphBuilder):
        self.graph = builder.graph

    def get_document_entities(self, document_id: str) -> dict:
        if document_id not in self.graph:
            return {}

        entities = {
            "monetary_values": [],
            "percentages": [],
            "dates": [],
            "organizations": [],
        }

        for _, neighbor in self.graph.edges(document_id):
            if self.graph.nodes[neighbor].get("node_type") == "chunk":
                for _, entity_node in self.graph.edges(neighbor):
                    node_data = self.graph.nodes[entity_node]
                    node_type = node_data.get("node_type")
                    if node_type in entities:
                        value = node_data.get("value")
                        if value and value not in entities[node_type]:
                            entities[node_type].append(value)

        return entities

    def find_common_entities(self, doc_id_1: str, doc_id_2: str) -> dict:
        entities_1 = self.get_document_entities(doc_id_1)
        entities_2 = self.get_document_entities(doc_id_2)

        common = {}
        for entity_type in entities_1:
            set_1 = set(entities_1.get(entity_type, []))
            set_2 = set(entities_2.get(entity_type, []))
            common[entity_type] = list(set_1 & set_2)

        return common
