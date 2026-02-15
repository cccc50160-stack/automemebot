"""Trend aggregator — combines all trend sources."""
from modules.database.operations import DatabaseManager
from .groq_trends import GroqTrendCollector
from .google_trends import GoogleTrendsCollector
from .reddit_scraper import RedditScraper


class TrendAggregator:
    def __init__(self, groq_collector: GroqTrendCollector, db: DatabaseManager, logger=None):
        self.groq_collector = groq_collector
        self.google_collector = GoogleTrendsCollector(logger)
        self.reddit_scraper = RedditScraper(logger)
        self.db = db
        self.logger = logger

    async def collect_all(self) -> list[dict]:
        """Collect trends from all available sources."""
        all_trends = []

        # Primary: Groq-generated trends (always available)
        groq_trends = await self.groq_collector.collect(count=8)
        all_trends.extend(groq_trends)

        # Secondary: Google Trends (free, no key)
        google_trends = await self.google_collector.collect()
        all_trends.extend(google_trends)

        # Optional: Reddit (needs API key)
        reddit_trends = await self.reddit_scraper.collect()
        all_trends.extend(reddit_trends)

        # Deduplicate by topic similarity (simple)
        seen_topics = set()
        unique_trends = []
        for t in all_trends:
            topic_lower = t["topic"].lower().strip()
            if topic_lower not in seen_topics:
                seen_topics.add(topic_lower)
                unique_trends.append(t)

        # Sort by relevance
        unique_trends.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Save to database
        if unique_trends:
            await self.db.save_trends(unique_trends)

        if self.logger:
            sources = {}
            for t in unique_trends:
                src = t.get("source", "unknown")
                sources[src] = sources.get(src, 0) + 1

            source_lines = "\n".join(f"- {src}: {cnt} trends" for src, cnt in sources.items())
            top_topics = ", ".join(t["topic"] for t in unique_trends[:5])

            await self.logger.log_system_event(
                "Trends Collection Completed",
                f"Total: {len(unique_trends)} unique trends\n\n"
                f"Sources:\n{source_lines}\n\n"
                f"Top-5: {top_topics}"
            )

        return unique_trends
