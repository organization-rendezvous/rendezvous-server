class MdAssembler:

    def build(self, topics, trends, links):

        link_map = {}
        for link in links:
            link_map.setdefault(link["trend_id"], []).append(link)

        for t in trends:
            if "links" not in t:
                t["links"] = link_map.get(t["id"], [])

        topic_map = {}

        return {
            "topics": topics,
            "trends": trends,
            "links": links
        }