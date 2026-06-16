from app.schemas.trends import AnalysisTopicStatusResponse
from fastapi import APIRouter, BackgroundTasks, Response, status
import logging

from app.db.repositories import repository
from app.schemas.trends import (
    AnalysisJobResultResponse,
    AnalysisJobStatusResponse,
    AnalyzeTrendRequest,
    AnalyzeTrendResponse,
    TopicTrendResult,
    TrendDetailResponse,
    TrendLinkResponse,
    TrendScoreResponse,
    TrendSummaryItem,
)
from app.services import run_analysis_job, start_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trends", tags=["trends"])


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_trends(request: AnalyzeTrendRequest, background_tasks: BackgroundTasks) -> AnalyzeTrendResponse:
    logger.info(f"▶ POST /analyze | topics={request.topics} period={request.period}")
    job = start_analysis(request)
    background_tasks.add_task(run_analysis_job, job["id"])
    logger.info(f"job 생성됨 | job_id={job['id']}")
    return AnalyzeTrendResponse(job_id=job["id"], status=job["status"], started_at=job["started_at"])


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> AnalysisJobStatusResponse:
    data = repository.get_job_status(job_id)
    # logger.info(
    #     f"🔄 GET /jobs/{job_id} | status={data['job']['status']} progress={data.get('progress', 0)}%"
    # )
    return AnalysisJobStatusResponse(
        job_id=data["job"]["id"],
        status=data["job"]["status"],         
        progress=data.get("progress", 0),

        topics=[
            AnalysisTopicStatusResponse(
                topic_id=topic["id"],
                name=topic["topic_name"],

                status=topic["status"],       
                current_step=topic.get("step"),

                error_message=topic.get("error_message"),
            )
            for topic in data.get("topics", [])
        ],
    )


@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str, response: Response):
    data = repository.get_job_result(job_id)
   

    if data["job"]["status"] not in {
        "completed",
        "partial_failed",
        "failed",
    }:
        response.status_code = status.HTTP_202_ACCEPTED

    return _result_response(data)


@router.get("/latest")
async def get_latest_result(user_id: str = "personal-user") -> AnalysisJobResultResponse:
    logger.info(f"🕐 GET /latest | user_id={user_id}")
    return _result_response(repository.get_latest_result(user_id))


@router.get("/{trend_id}")
async def get_trend_detail(trend_id: str) -> TrendDetailResponse:
    logger.info(f"🔍 GET /trends/{trend_id}")
    data = repository.get_trend_detail(trend_id)
    trend = data["trend"]
    return TrendDetailResponse(
        trend_id=trend["id"],
        title=trend["title"],
        topic=data["topic"]["topic_name"],
        rank=trend["rank"],
        score=trend["final_score"],
        summary=trend["summary"],
        detail_summary=trend["detail_summary"],
        ai_comment=trend["ai_comment"],
        keywords=trend["keywords"],
        scores=TrendScoreResponse(**{key: value for key, value in data["scores"].items() if key != "trend_id" and key != "created_at"}),
        links=[TrendLinkResponse(**_link_payload(link)) for link in data["links"]],
    )


def _result_response(data: dict) -> AnalysisJobResultResponse:
    return AnalysisJobResultResponse(
        job_id=data["job"]["id"],
        status=data["job"]["status"],
        topics=[
            TopicTrendResult(
                topic_id=topic_result["topic"]["id"],
                name=topic_result["topic"]["topic_name"],
                trends=[
                    TrendSummaryItem(
                        trend_id=trend["id"],
                        rank=trend["rank"],
                        title=trend["title"],
                        summary=trend["summary"],
                        score=trend["final_score"],
                        is_rising=trend["final_score"] >= 70,
                    )
                    for trend in topic_result["trends"]
                ],
            )
            for topic_result in data["topics"]
        ],
    )


def _link_payload(link: dict) -> dict:
    return {
        "title": link["title"],
        "url": link["url"],
        "source_name": link["source_name"],
        "source_type": link["source_type"],
        "published_at": link.get("published_at"),
        "summary": link.get("summary"),
        "relevance_score": link.get("relevance_score"),
        "credibility_score": link.get("credibility_score"),
    }
