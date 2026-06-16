from app.core.config import TOPIC_KEYWORDS

def filter_documents_by_topic(
    documents: list[dict],
    topic: str,
) -> list[dict]:
    return documents

    keywords = TOPIC_KEYWORDS.get(topic)

    if not keywords:
        return documents

    filtered = []

    for doc in documents:
        text = (
            doc.get("title", "")
            + " "
            + doc.get("summary", "")
            + " "
            + doc.get("raw_text", "")
        ).lower()

        if any(keyword.lower() in text for keyword in keywords):
            filtered.append(doc)


    return filtered