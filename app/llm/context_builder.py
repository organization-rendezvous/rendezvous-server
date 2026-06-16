def build_llm_context(documents: list[dict], limit: int = 3) -> str:
    compressed = []

    for d in documents[:limit]:
        compressed.append(
            f"{d.get('title','')} | {d.get('summary','')}"
        )

    return "\n".join(compressed)