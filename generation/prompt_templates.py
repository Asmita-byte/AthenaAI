SYSTEM_PROMPT = """You are a precise document analysis assistant. You answer questions strictly using the provided context from documents.

Rules:
- Only use information present in the provided context.
- If the context does not contain enough information to answer, say so clearly.
- Always cite which source (page number, table, or figure) supports each claim.
- Be concise and factual. Do not speculate beyond the given context.
- If multiple documents are provided, distinguish between them clearly when relevant."""


def build_qa_prompt(query: str, context_chunks: list[dict]) -> str:
    context_sections = []

    for i, chunk in enumerate(context_chunks, start=1):
        payload = chunk.get("payload", {})
        source = payload.get("source_filename", "unknown")
        page = payload.get("page_number", "N/A")
        chunk_type = payload.get("chunk_type", "text")
        content = payload.get("content", "")

        context_sections.append(
            f"[Source {i}] (file: {source}, page: {page}, type: {chunk_type})\n{content}"
        )

    context_text = "\n\n".join(context_sections)

    prompt = f"""Context from documents:

{context_text}

---

Question: {query}

Answer the question using only the context above. Cite the source number(s) for each claim."""

    return prompt