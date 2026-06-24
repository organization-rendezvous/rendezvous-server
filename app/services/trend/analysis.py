from app.core.config import get_settings
from app.db.repository_factory import repository
from app.graph import run_topic_analysis
from app.schemas.trends import AnalyzeTrendRequest
from app.graph.trend.state import TrendAnalysisInputState, TrendAnalysisState
from app.core.types import JobStatus, TopicStatus
import logging
logger = logging.getLogger(__name__)


def start_analysis(request: AnalyzeTrendRequest) -> dict:
    settings = get_settings()
    user_settings = repository.get_user_settings(request.user_id)

    topics = (
        request.topics
        or [*user_settings["enabled_topics"], *user_settings["custom_topics"]]
        or settings.default_topics
    )

    period = request.period or user_settings["period"] or settings.default_period
    result_limit = request.result_limit or user_settings["result_limit"] or settings.default_result_limit
    sources = request.sources or user_settings["enabled_sources"] or settings.default_sources

    logger.info(
        f"🚀 분석 시작 | topics={topics} period={period} limit={result_limit} sources={sources}"
    )

    job = repository.create_analysis_job(
        user_id=request.user_id,
        period=period,
        result_limit=result_limit,
        sources=sources,
    )

    for topic in topics:
        repository.create_analysis_topic(job_id=job["id"], topic_name=topic)

    logger.info(f"📋 job 등록 완료 | job_id={job['id']} | 주제 수={len(topics)}")
    return job


# 핵심: Input → Pipeline state 변환
def build_initial_state(input_state: TrendAnalysisInputState) -> TrendAnalysisState:
    return {
        **input_state,

        "raw_documents": [],
        "cleaned_documents": [],

        "trend_candidates": [],
        "scored_trends": [],
        "summarized_trends": [],

        "final_trends": [],

        "errors": [],
        "retry_count": 0,
        "next_action": "",
        "trend_embedding": None,
    }


async def run_analysis_job(job_id: str) -> None:
    status = repository.get_job_status(job_id)
    job = status["job"]
    topics = status["topics"]

    logger.info(
        f"⚙️  분석 실행 시작 | job_id={job_id} | 주제={[t['topic_name'] for t in topics]}"
    )

    repository.update_analysis_job_status(job_id, JobStatus.RUNNING)

    for topic in topics:
        logger.info(f"  → [{topic['topic_name']}] 분석 시작")

        input_state = TrendAnalysisInputState(
            job_id=job_id,
            topic_id=topic["id"],
            topic=topic["topic_name"],
            period=job["period"],
            result_limit=job["result_limit"],
            sources=job["sources"],
        )

        result = await run_topic_analysis(build_initial_state(input_state))

        if result.get("errors") and topic_has_failed(topic["id"]):
            logger.warning(
                f"  ✗ [{topic['topic_name']}] 분석 실패 | errors={result.get('errors')}"
            )
        else:
            logger.info(f"  ✓ [{topic['topic_name']}] 분석 완료")

    latest = repository.get_job_status(job_id)
    failed_topics = [
        t for t in latest["topics"]
        if t["status"] == TopicStatus.FAILED.value
    ]

    if len(failed_topics) == len(latest["topics"]):
        logger.error(f"❌ 전체 실패 | job_id={job_id}")
        repository.update_analysis_job_status(
            job_id, JobStatus.FAILED, "모든 주제 분석에 실패했습니다."
        )

    elif failed_topics:
        logger.warning(
            f"⚠️  일부 실패 | job_id={job_id} | 실패={[t['topic_name'] for t in failed_topics]}"
        )
        repository.update_analysis_job_status(job_id, JobStatus.PARTIAL_FAILED)

    else:
        logger.info(f"🎉 전체 완료 | job_id={job_id}")
        repository.update_analysis_job_status(job_id, JobStatus.COMPLETED)


def topic_has_failed(topic_id: str) -> bool:
    try:
        return repository._topic(topic_id)["status"] == TopicStatus.FAILED.value
    except Exception:
        return True