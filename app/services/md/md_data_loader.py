class MdDataLoader:
    def __init__(self, repository):
        self.repository = repository

    def load(self, job_id: str) -> dict:
        topics = (
            self.repository.client.table("analysis_topics")
            .select("*")
            .eq("job_id", job_id)
            .execute()
            .data
        )

        trends = (
            self.repository.client.table("trends")
            .select("*")
            .eq("job_id", job_id)
            .execute()
            .data
        )

        links = (
            self.repository.client.table("trend_links")
            .select("*")
            .execute()
            .data
        )

        # 1차 join (DataLoader 책임)
        for topic in topics:
            topic["trends"] = [
                t for t in trends if t["topic_id"] == topic["id"]
            ]

        for trend in trends:
            trend["links"] = [
                l for l in links if l["trend_id"] == trend["id"]
            ]

        return {
            "topics": topics,
            "trends": trends,
            "links": links,
        }