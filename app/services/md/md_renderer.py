from datetime import datetime, timezone


class MdRenderer:
    def render(self, data: dict, settings: dict) -> str:
        md = []

        md.append(self._header())

        for topic in data["topics"]:
            if topic["topic_name"] not in settings["enabled_topics"]:
                continue

            md.append(self._render_topic(topic, settings))

        return "\n\n".join(md)

    def _header(self):
        today = datetime.now(timezone.utc).date().isoformat()
        return f"# {today} 데일리 브리핑"

    def _render_topic(self, topic: dict, settings: dict) -> str:
        lines = [f"## {topic['topic_name']}"]

        trends = sorted(topic.get("trends", []), key=lambda x: x["rank"])

        for trend in trends[: settings["result_limit"]]:
            lines.append(self._render_trend(trend, settings))

        return "\n".join(lines)

    def _render_trend(self, trend: dict, settings: dict) -> str:
        lines = []

        lines.append(f"### {trend['title']}")

        if settings.get("include_summary"):
            lines.append(f"- {trend.get('summary', '')}")

        if settings.get("include_detail_summary"):
            lines.append(f"- {trend.get('detail_summary', '')}")

        if settings.get("include_keywords"):
            lines.append(f"키워드: {', '.join(trend.get('keywords', []))}")

        if settings.get("include_links"):
            for link in trend.get("links", [])[:3]:
                lines.append(f"- {link.get('title')} ({link.get('url')})")

        lines.append("---")

        return "\n".join(lines)