class ToolSelector:

    METADATA_KEYWORDS = [
        "author", "title", "when was", "who wrote", "published", "date",
        "page count", "how many pages",
    ]

    def select_tools(self, query: str) -> list[str]:
        query_lower = query.lower()

        selected = {
            "text_retriever",
            "table_retriever",
            "figure_retriever",
            "chart_retriever",
        }

        if any(keyword in query_lower for keyword in self.METADATA_KEYWORDS):
            selected.add("metadata_retriever")

        return list(selected)