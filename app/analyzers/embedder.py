from app.embeddings.batch import embed_batch


def embed_candidates(candidates: list[dict]) -> list[dict]:
    texts = []

    for c in candidates:
        text = " ".join([
            c.get("title", ""),
            " ".join(c.get("keywords", []))
        ])
        texts.append(text)

    embeddings = embed_batch(texts)

    for c, emb in zip(candidates, embeddings):
        c["embedding"] = emb

    return candidates