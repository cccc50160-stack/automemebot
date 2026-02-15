"""Reddit trend scraper (stub — requires Reddit API credentials)."""
from config.settings import settings


class RedditScraper:
    def __init__(self, logger=None):
        self.logger = logger
        self.enabled = bool(settings.reddit_client_id and settings.reddit_client_secret)

    async def collect(self, limit: int = 10) -> list[dict]:
        """Collect trending meme topics from Reddit."""
        if not self.enabled:
            return []

        try:
            import praw

            reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
            )

            trends = []
            subreddits = ["memes", "dankmemes", "me_irl"]

            for sub_name in subreddits:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.hot(limit=limit // len(subreddits)):
                    trends.append({
                        "topic": post.title,
                        "keywords": post.title.lower().split()[:5],
                        "context": f"Hot on r/{sub_name} ({post.score} upvotes)",
                        "category": "memes",
                        "source": "reddit",
                        "relevance_score": min(1.0, post.score / 10000),
                    })

            return trends

        except ImportError:
            if self.logger:
                await self.logger.log_warning(
                    "Reddit Unavailable",
                    "praw package not installed. Install with: pip install praw"
                )
            return []
        except Exception as e:
            if self.logger:
                await self.logger.log_warning(
                    "Reddit Error",
                    f"Failed to collect from Reddit: {e}"
                )
            return []
