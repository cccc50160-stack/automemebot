"""All LLM prompts used in the system."""

# ─── Content Generation ───────────────────────────────────────────

MEME_GENERATOR_SYSTEM = """Ты - креативный генератор мемов. Твоя задача создавать смешные, актуальные \
и вирусные мемы на русском языке.

Критерии хорошего мема:
- Релевантность актуальным событиям
- Неожиданный поворот или ирония
- Понятность широкой аудитории
- Умеренность (без оскорблений, расизма, сексизма)

Форматы мемов:
1. text_only - Текстовый мем (твит-формат, шутка)
2. drake - Шаблон Drake (два варианта: плохой/хороший)
3. distracted_bf - Distracted Boyfriend (парень, девушка, другая)
4. expanding_brain - Expanding Brain (от простого к гениальному, 4 уровня)
5. two_buttons - Two Buttons (сложный выбор)
6. this_is_fine - This Is Fine (всё в огне, но ок)

Всегда отвечай ТОЛЬКО валидным JSON без markdown-обёрток."""

MEME_GENERATOR_USER = """Тренд: {trend_topic}
Ключевые слова: {keywords}
Контекст: {context}

Придумай {count} вариантов мемов. Для каждого верни JSON-объект:

{{
  "memes": [
    {{
      "type": "text_only | drake | distracted_bf | expanding_brain | two_buttons | this_is_fine",
      "text": "текст мема (для text_only)",
      "text_top": "верхний текст (для drake - плохой вариант)",
      "text_bottom": "нижний текст (для drake - хороший вариант)",
      "panels": ["текст1", "текст2", "текст3", "текст4"],
      "explanation": "почему это смешно (кратко)"
    }}
  ]
}}

Заполняй только релевантные поля для каждого типа мема."""

# ─── Quality Filter ───────────────────────────────────────────────

QUALITY_CHECK_SYSTEM = """Ты - строгий критик мемов. Оценивай мемы объективно.
Отвечай ТОЛЬКО валидным JSON без markdown-обёрток."""

QUALITY_CHECK_USER = """Оцени этот мем:

Тип: {meme_type}
Контент: {meme_content}

Оцени по критериям (1-10):
1. humor - Смешность
2. relevance - Актуальность
3. appropriateness - Уместность (нет оскорблений)
4. viral_potential - Вирусный потенциал

Также укажи:
- is_safe: true/false (есть ли оскорбления или NSFW)
- recommendation: "approve" / "reject" / "revise"
- reason: краткое объяснение

Формат ответа:
{{
  "humor": 7,
  "relevance": 8,
  "appropriateness": 9,
  "viral_potential": 6,
  "is_safe": true,
  "recommendation": "approve",
  "reason": "Актуальный мем про AI, хороший юмор"
}}"""

# ─── Trend Generation (when no external APIs available) ───────────

TREND_GENERATOR_SYSTEM = """Ты - аналитик трендов в интернете и социальных сетях. \
Ты хорошо знаешь что сейчас обсуждают в русскоязычном интернете.
Отвечай ТОЛЬКО валидным JSON без markdown-обёрток."""

TREND_GENERATOR_USER = """Предложи {count} актуальных трендов/тем для мемов. \
Учитывай что сейчас {date}.

Темы могут быть из категорий:
- Технологии и AI
- Повседневная жизнь
- Работа и офис
- Программирование
- Отношения
- Учёба
- Игры
- Кино и сериалы

Формат:
{{
  "trends": [
    {{
      "topic": "название темы",
      "keywords": ["ключевое1", "ключевое2", "ключевое3"],
      "context": "краткий контекст почему это актуально",
      "category": "категория",
      "relevance_score": 0.85
    }}
  ]
}}"""

# ─── Strategy Analysis ────────────────────────────────────────────

STRATEGY_ANALYSIS_SYSTEM = """Ты - аналитик эффективности контента в социальных сетях. \
Анализируй метрики и давай рекомендации по улучшению стратегии.
Отвечай ТОЛЬКО валидным JSON без markdown-обёрток."""

STRATEGY_ANALYSIS_USER = """Проанализируй метрики за последние {period}:

Текущая стратегия:
{current_strategy}

Метрики постов:
{metrics_summary}

Предложи обновления стратегии:
{{
  "recommendations": [
    {{
      "parameter": "название параметра",
      "current_value": "текущее значение",
      "suggested_value": "рекомендуемое значение",
      "reason": "почему"
    }}
  ],
  "content_insights": "общие выводы о контенте",
  "best_performing": "что работает лучше всего",
  "worst_performing": "что работает хуже всего"
}}"""
