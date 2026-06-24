from app.db.repository_factory import repository


def update_status(
    state,
    status,
    action,
    **kwargs,
):
    repository.update_analysis_topic_status(
        state.get("topic_id"),
        status,
        action,
        **kwargs,
    )


#chat
def strip_code_block(content: str) -> str:
    if content.startswith("```json"):
        content = content.split("```json")[1].split("```")[0].strip()
    elif content.startswith("```"):
        content = content.split("```")[1].split("```")[0].strip()
    return content
