from agents.tools.figure_tool import FigureTool
from backend.core.logging import get_logger

logger = get_logger(__name__)


class ChartTool(FigureTool):

    name = "chart_retriever"
    description = "Retrieves relevant charts and data visualizations from documents using cross-modal search."

    def run(self, query: str, document_ids: list[str] | None = None, top_k: int = 5) -> list[dict]:
        chart_query = f"chart graph data visualization: {query}"
        logger.info("ChartTool invoked", query=query[:50])
        return super().run(chart_query, document_ids=document_ids, top_k=top_k)