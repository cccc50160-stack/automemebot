"""Message formatters for all log types."""
from datetime import datetime
from modules.utils.helpers import format_number, truncate, format_reactions


class LogFormatter:
    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%H:%M:%S %d.%m.%Y")

    @staticmethod
    def _time() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _date() -> str:
        return datetime.now().strftime("%d.%m.%Y")

    # ─── System Events ─────────────────────────────────────────────

    def format_system_event(self, event_type: str, details: str) -> str:
        return (
            f"\u2139\ufe0f <b>SYSTEM EVENT</b>\n\n"
            f"<b>\u0422\u0438\u043f:</b> {event_type}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._now()}\n\n"
            f"<b>\u0414\u0435\u0442\u0430\u043b\u0438:</b>\n{details}"
        )

    def format_info(self, title: str, details: str) -> str:
        return (
            f"\u2139\ufe0f <b>{title}</b>\n\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"{details}"
        )

    # ─── Post Published ────────────────────────────────────────────

    def format_successful_post(self, data: dict) -> str:
        preview = truncate(data.get("preview", ""), 200)
        quality = data.get("quality_score", "?")
        relevance = data.get("relevance_score", "?")

        text = (
            f"\u2705 <b>\u041f\u041e\u0421\u0422 \u041e\u041f\u0423\u0411\u041b\u0418\u041a\u041e\u0412\u0410\u041d</b>\n\n"
            f"<b>ID:</b> {data.get('post_id', '?')}\n"
            f"<b>\u0422\u0438\u043f:</b> {data.get('content_type', '?')}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"<b>\u041a\u043e\u043d\u0442\u0435\u043d\u0442:</b>\n{preview}\n\n"
            f"<b>\u041c\u0435\u0442\u0440\u0438\u043a\u0438 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u0438:</b>\n"
            f"- Quality Score: {quality}/10\n"
            f"- Relevance: {relevance}/10\n"
            f"- \u0422\u0435\u043c\u0430: {data.get('trend_topic', '?')}"
        )

        link = data.get("channel_link")
        if link:
            text += f'\n\n\U0001f517 <a href="{link}">\u041f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u0432 \u043a\u0430\u043d\u0430\u043b\u0435</a>'

        return text

    # ─── Post Metrics ──────────────────────────────────────────────

    def format_post_metrics(self, post_id: int | str, m: dict) -> str:
        reactions_str = format_reactions(m.get("reactions", {}))
        return (
            f"\U0001f4ca <b>\u041c\u0415\u0422\u0420\u0418\u041a\u0418 \u041f\u041e\u0421\u0422\u0410 #{post_id}</b>\n\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f \u0441 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438:</b> {m.get('time_elapsed', '?')}\n\n"
            f"<b>\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430:</b>\n"
            f"\U0001f441 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b: {format_number(m.get('views', 0))}"
            f" (+{format_number(m.get('views_growth', 0))})\n"
            f"\U0001f4e4 \u0420\u0435\u043f\u043e\u0441\u0442\u044b: {m.get('forwards', 0)}\n"
            f"\U0001f4ac \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0438: {m.get('comments', 0)}\n\n"
            f"<b>\u0420\u0435\u0430\u043a\u0446\u0438\u0438:</b>\n{reactions_str}\n\n"
            f"<b>Engagement Rate:</b> {m.get('engagement_rate', 0):.2%}\n"
            f"<b>Performance Score:</b> {m.get('performance_score', 0)}/10"
        )

    # ─── Warning ───────────────────────────────────────────────────

    def format_warning(self, warning_type: str, details: str) -> str:
        return (
            f"\u26a0\ufe0f <b>WARNING</b>\n\n"
            f"<b>\u0422\u0438\u043f:</b> {warning_type}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"<b>\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:</b>\n{details}"
        )

    # ─── Error ─────────────────────────────────────────────────────

    def format_error(self, error_type: str, error: Exception,
                     tb: str = "", context: dict = None) -> str:
        ctx = context or {}
        tb_short = truncate(tb, 500) if tb else ""

        text = (
            f"\u274c <b>ERROR</b>\n\n"
            f"<b>\u0422\u0438\u043f:</b> {error_type}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"<b>\u041e\u0448\u0438\u0431\u043a\u0430:</b>\n<code>{str(error)}</code>\n"
        )

        if ctx.get("module"):
            text += f"\n<b>\u041c\u043e\u0434\u0443\u043b\u044c:</b> {ctx['module']}"
        if ctx.get("function"):
            text += f"\n<b>\u0424\u0443\u043d\u043a\u0446\u0438\u044f:</b> {ctx['function']}"

        if tb_short:
            text += f"\n\n<b>Traceback:</b>\n<pre>{tb_short}</pre>"

        return text

    # ─── Critical ──────────────────────────────────────────────────

    def format_critical(self, critical_type: str, details: str) -> str:
        return (
            f"\U0001f6a8 <b>CRITICAL ALERT</b> \U0001f6a8\n\n"
            f"<b>\u0422\u0438\u043f:</b> {critical_type}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"<b>\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435:</b>\n{details}\n\n"
            f"\u26a0\ufe0f <b>\u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u0441\u0440\u043e\u0447\u043d\u043e\u0435 \u0432\u043c\u0435\u0448\u0430\u0442\u0435\u043b\u044c\u0441\u0442\u0432\u043e</b>"
        )

    # ─── Strategy Update ───────────────────────────────────────────

    def format_strategy_update(self, old: dict, new: dict, reason: str) -> str:
        diff_lines = self._strategy_diff(old, new)
        return (
            f"\U0001f504 <b>\u0421\u0422\u0420\u0410\u0422\u0415\u0413\u0418\u042f \u041e\u0411\u041d\u041e\u0412\u041b\u0415\u041d\u0410</b>\n\n"
            f"<b>\u041f\u0440\u0438\u0447\u0438\u043d\u0430:</b> {reason}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u044f:</b>\n\n{diff_lines}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\u041f\u0435\u0440\u0438\u043e\u0434 \u0442\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f:</b> 48 \u0447\u0430\u0441\u043e\u0432"
        )

    @staticmethod
    def _strategy_diff(old: dict, new: dict) -> str:
        lines = []
        for key in new:
            if key in old and old[key] != new[key]:
                lines.append(f"\u2022 {key}: {old[key]} \u2192 {new[key]}")
        return "\n".join(lines) if lines else "\u041d\u0435\u0442 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439"

    # ─── A/B Test Results ──────────────────────────────────────────

    def format_ab_test_results(self, data: dict) -> str:
        va = data.get("variant_a", {})
        vb = data.get("variant_b", {})
        return (
            f"\U0001f9ea <b>A/B \u0422\u0415\u0421\u0422 \u0417\u0410\u0412\u0415\u0420\u0428\u0415\u041d</b>\n\n"
            f"<b>\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435:</b> {data.get('test_name', '?')}\n"
            f"<b>\u041f\u0435\u0440\u0438\u043e\u0434:</b> {data.get('duration', '?')}\n"
            f"<b>\u0412\u044b\u0431\u043e\u0440\u043a\u0430:</b> {data.get('sample_size', '?')} \u043f\u043e\u0441\u0442\u043e\u0432\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\u0412\u0430\u0440\u0438\u0430\u043d\u0442 A:</b> {va.get('description', '')}\n"
            f"\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b: {format_number(va.get('avg_views', 0))}\n"
            f"Engagement: {va.get('engagement', 0):.2%}\n\n"
            f"<b>\u0412\u0430\u0440\u0438\u0430\u043d\u0442 B:</b> {vb.get('description', '')}\n"
            f"\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u044b: {format_number(vb.get('avg_views', 0))}\n"
            f"Engagement: {vb.get('engagement', 0):.2%}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\u041f\u043e\u0431\u0435\u0434\u0438\u0442\u0435\u043b\u044c:</b> {data.get('winner', '?')}\n"
            f"<b>\u0420\u0430\u0437\u043d\u0438\u0446\u0430:</b> {data.get('difference', 0):.1f}%\n\n"
            f"<b>\u0420\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u044f:</b>\n{data.get('recommendation', '')}"
        )

    # ─── Anomaly ───────────────────────────────────────────────────

    def format_anomaly(self, data: dict) -> str:
        return (
            f"\U0001f514 <b>\u0410\u041d\u041e\u041c\u0410\u041b\u0418\u042f \u041e\u0411\u041d\u0410\u0420\u0423\u0416\u0415\u041d\u0410</b>\n\n"
            f"<b>\u0422\u0438\u043f:</b> {data.get('type', '?')}\n"
            f"<b>\u041c\u0435\u0442\u0440\u0438\u043a\u0430:</b> {data.get('metric', '?')}\n"
            f"<b>\u0412\u0440\u0435\u043c\u044f:</b> {self._time()}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\u0422\u0435\u043a\u0443\u0449\u0435\u0435:</b> {data.get('current_value', '?')}\n"
            f"<b>\u041e\u0436\u0438\u0434\u0430\u0435\u043c\u043e\u0435:</b> {data.get('expected_value', '?')}\n"
            f"<b>\u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0435:</b> {data.get('deviation', 0):.1f}%\n\n"
            f"<b>\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435:</b> {data.get('auto_response', '\u041d\u0435\u0442')}"
        )

    # ─── Daily Report ──────────────────────────────────────────────

    def format_daily_report(self, s: dict) -> str:
        top = s.get("top_post", {})
        top_link = top.get("link", "")
        top_section = (
            f"\u0422\u043e\u043f-\u043f\u043e\u0441\u0442 \u0434\u043d\u044f:\n"
            f"\U0001f441 {format_number(top.get('views', 0))} \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432\n"
            f"\U0001f4e4 {top.get('forwards', 0)} \u0440\u0435\u043f\u043e\u0441\u0442\u043e\u0432"
        )
        if top_link:
            top_section += f'\n\U0001f517 <a href="{top_link}">\u041f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c</a>'

        return (
            f"\U0001f4c8 <b>\u0414\u041d\u0415\u0412\u041d\u041e\u0419 \u041e\u0422\u0427\u0415\u0422</b>\n"
            f"{self._date()}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\U0001f4ca \u041f\u0423\u0411\u041b\u0418\u041a\u0410\u0426\u0418\u0418</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e: {s.get('posts_count', 0)} \u043c\u0435\u043c\u043e\u0432\n"
            f"\u2705 \u0423\u0441\u043f\u0435\u0448\u043d\u043e: {s.get('successful_posts', 0)}\n"
            f"\u274c \u041e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u043e: {s.get('rejected_posts', 0)}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\U0001f465 \u0410\u0423\u0414\u0418\u0422\u041e\u0420\u0418\u042f</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"\u0412\u0441\u0435\u0433\u043e \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432: {format_number(s.get('total_views', 0))}\n"
            f"\u0421\u0440\u0435\u0434\u043d\u0438\u0439 \u043e\u0445\u0432\u0430\u0442: {format_number(s.get('avg_views_per_post', 0))}\n"
            f"\u041d\u043e\u0432\u044b\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u0447\u0438\u043a\u0438: +{s.get('new_subscribers', 0)}\n\n"
            f"{top_section}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\U0001f4c8 \u041c\u0415\u0422\u0420\u0418\u041a\u0418</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"\u0421\u0440\u0435\u0434\u043d\u0438\u0439 Engagement: {s.get('avg_engagement', 0):.2%}\n"
            f"Performance Score: {s.get('avg_performance', 0):.1f}/10\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\u2699\ufe0f \u0421\u0418\u0421\u0422\u0415\u041c\u0410</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"Uptime: {s.get('uptime', '?')}\n"
            f"API \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432: {s.get('api_calls', 0)}\n"
            f"\u041e\u0448\u0438\u0431\u043a\u0438: {s.get('errors_count', 0)}\n"
            f"\u041f\u0440\u0435\u0434\u0443\u043f\u0440\u0435\u0436\u0434\u0435\u043d\u0438\u044f: {s.get('warnings_count', 0)}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043e\u0442\u0447\u0435\u0442: \u0437\u0430\u0432\u0442\u0440\u0430 \u0432 23:00"
        )

    # ─── Weekly Report ─────────────────────────────────────────────

    def format_weekly_report(self, s: dict) -> str:
        return (
            f"\U0001f4ca <b>\u041d\u0415\u0414\u0415\u041b\u042c\u041d\u042b\u0419 \u041e\u0422\u0427\u0415\u0422</b>\n"
            f"{s.get('week_start', '?')} - {s.get('week_end', '?')}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\U0001f3af \u041a\u041b\u042e\u0427\u0415\u0412\u042b\u0415 \u041f\u041e\u041a\u0410\u0417\u0410\u0422\u0415\u041b\u0418</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"\U0001f4dd \u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e: {s.get('total_posts', 0)} \u043c\u0435\u043c\u043e\u0432\n"
            f"\U0001f441 \u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432: {format_number(s.get('total_views', 0))}\n"
            f"\U0001f465 \u041d\u043e\u0432\u044b\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u0447\u0438\u043a\u0438: +{s.get('new_subs', 0)}\n"
            f"\U0001f4c8 \u0420\u043e\u0441\u0442 \u0430\u0443\u0434\u0438\u0442\u043e\u0440\u0438\u0438: {s.get('growth_rate', 0):+.1f}%\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\U0001f3c6 \u041b\u0423\u0427\u0428\u0418\u0419 \u041f\u041e\u0421\u0422</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"\U0001f441 {format_number(s.get('best_post_views', 0))} \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u043e\u0432\n"
            f"\U0001f4e4 {s.get('best_post_forwards', 0)} \u0440\u0435\u043f\u043e\u0441\u0442\u043e\u0432\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"<b>\U0001f916 \u0421\u0418\u0421\u0422\u0415\u041c\u0410</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\n"
            f"Uptime: {s.get('weekly_uptime', '?')}\n"
            f"\u041e\u0448\u0438\u0431\u043a\u0438: {s.get('errors', 0)}\n"
            f"\u041a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435: {s.get('critical_errors', 0)}\n\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u043e\u0442\u0447\u0435\u0442: {s.get('next_report_date', '?')}"
        )
