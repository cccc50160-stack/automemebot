"""Google Trends collector using pytrends (free, no API key needed)."""
from pytrends.request import TrendReq


class GoogleTrendsCollector:
    def __init__(self, logger=None):
        self.logger = logger

    async def collect(self, geo: str = "RU") -> list[dict]:
        """Collect trending searches from Google Trends."""
        try:
            pytrends = TrendReq(hl="ru-RU", tz=180)
            trending = pytrends.trending_searches(pn="russia")

            if trending is None or trending.empty:
                return []

            trends = []
            for i, row in trending.head(10).iterrows():
                topic = str(row[0])
                trends.append({
                    "topic": topic,
                    "keywords": [topic],
                    "context": f"Trending in Google search ({geo})",
                    "category": "trending",
                    "source": "google_trends",
                    "relevance_score": max(0.5, 1.0 - i * 0.05),
                })

            return trends

        except Exception as e:
            if self.logger:
                await self.logger.log_warning(
                    "Google Trends Error",
                    f"Failed to collect trends: {e}"
                )
            return []
