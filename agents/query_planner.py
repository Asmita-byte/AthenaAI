from backend.core.logging import get_logger
from agents.tool_selector import ToolSelector
from agents.evidence_aggregator import EvidenceAggregator
from agents.tools.text_tool import TextTool
from agents.tools.table_tool import TableTool
from agents.tools.figure_tool import FigureTool
from agents.tools.chart_tool import ChartTool
from agents.tools.metadata_tool import MetadataTool

logger = get_logger(__name__)


class QueryPlanner:

    def __init__(self):
        self.tool_selector = ToolSelector()
        self.evidence_aggregator = EvidenceAggregator()

        self.tools = {
            "text_retriever": TextTool(),
            "table_retriever": TableTool(),
            "figure_retriever": FigureTool(),
            "chart_retriever": ChartTool(),
        }
        self.metadata_tool = MetadataTool()

    async def plan_and_execute(
        self,
        query: str,
        document_ids: list[str] | None = None,
        db=None,
    ) -> dict:
        logger.info("Query planning started", query=query[:50])

        selected_tool_names = self.tool_selector.select_tools(query)

        tool_results = {}

        for tool_name in selected_tool_names:
            if tool_name == "metadata_retriever":
                if db is not None:
                    tool_results[tool_name] = await self.metadata_tool.run(
                        db=db, document_ids=document_ids
                    )
                continue

            tool = self.tools.get(tool_name)
            if tool is None:
                continue

            try:
                tool_results[tool_name] = tool.run(query, document_ids=document_ids)
            except Exception as e:
                logger.warning(f"Tool {tool_name} failed", error=str(e))
                tool_results[tool_name] = []

        evidence = self.evidence_aggregator.aggregate(tool_results)

        logger.info(
            "Query planning complete",
            tools_used=selected_tool_names,
            total_evidence=evidence["total_evidence_count"],
        )

        return {
            "query": query,
            "tools_used": selected_tool_names,
            "evidence": evidence,
        }