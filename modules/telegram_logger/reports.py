"""Report generation for daily and weekly summaries."""
from datetime import datetime, timedelta
from modules.utils.helpers import format_number


class ReportGenerator:
    def __init__(self, db):
        self.db = db

    async def generate_daily_stats(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        posts = await self.db.get_posts_since(today_start)
        top_post = await self.db.get_top_post(today_start)
        error_count = await self.db.get_error_count_today()
        api_usage = await self.db.get_api_usage_today()

        published = [p for p in posts if p.published_at is not None]
        total_views = sum(p.views or 0 for p in published)
        avg_engagement = (
            sum(p.engagement_rate or 0 for p in published) / len(published)
            if published else 0
        )
        avg_performance = (
            sum(p.performance_score or 0 for p in published) / len(published)
            if published else 0
        )

        text_count = sum(1 for p in published if p.content_type == "text_only")
        visual_count = len(published) - text_count

        top_data = {}
        if top_post:
            top_data = {
                "views": top_post.views or 0,
                "forwards": top_post.forwards or 0,
                "link": "",
            }

        groq = api_usage.get("groq", {"calls": 0, "total_tokens": 0})

        return {
            "posts_count": len(published),
            "successful_posts": len(published),
            "rejected_posts": 0,
            "text_memes": text_count,
            "visual_memes": visual_count,
            "text_percentage": (text_count / len(published) * 100) if published else 0,
            "visual_percentage": (visual_count / len(published) * 100) if published else 0,
            "total_views": total_views,
            "avg_views_per_post": total_views // len(published) if published else 0,
            "new_subscribers": 0,
            "top_post": top_data,
            "avg_engagement": avg_engagement,
            "avg_performance": avg_performance,
            "uptime": "N/A",
            "api_calls": groq["calls"],
            "groq_tokens": groq["total_tokens"],
            "errors_count": error_count,
            "warnings_count": 0,
        }

    async def generate_weekly_stats(self) -> dict:
        week_start = datetime.utcnow() - timedelta(days=7)
        posts = await self.db.get_posts_since(week_start)
        published = [p for p in posts if p.published_at is not None]

        total_views = sum(p.views or 0 for p in published)
        top_post = await self.db.get_top_post(week_start)

        return {
            "week_start": week_start.strftime("%d.%m"),
            "week_end": datetime.utcnow().strftime("%d.%m"),
            "total_posts": len(published),
            "total_views": total_views,
            "new_subs": 0,
            "growth_rate": 0.0,
            "best_post_views": top_post.views if top_post else 0,
            "best_post_forwards": top_post.forwards if top_post else 0,
            "weekly_uptime": "N/A",
            "errors": 0,
            "critical_errors": 0,
            "next_report_date": (datetime.utcnow() + timedelta(days=7)).strftime("%d.%m.%Y"),
        }
