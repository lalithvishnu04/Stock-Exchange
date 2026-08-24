"""News fetching + sentiment analysis (VADER + optional OpenAI)."""
import re
from typing import Optional
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.config import settings


class SentimentService:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self._news_client: Optional[NewsApiClient] = None
        if settings.NEWS_API_KEY:
            self._news_client = NewsApiClient(api_key=settings.NEWS_API_KEY)

    def _vader_sentiment(self, text: str) -> tuple[str, float]:
        scores = self.vader.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            return "POSITIVE", compound
        if compound <= -0.05:
            return "NEGATIVE", compound
        return "NEUTRAL", compound

    def analyze_text(self, text: str) -> dict:
        label, score = self._vader_sentiment(text)
        return {"sentiment": label, "score": round(score, 4)}

    def get_news_for_symbol(self, symbol: str, company_name: str = "") -> list[dict]:
        if not self._news_client:
            return []
        query = company_name or symbol
        try:
            response = self._news_client.get_everything(
                q=f"{query} stock India",
                language="en",
                sort_by="publishedAt",
                page_size=10,
            )
            articles = response.get("articles", [])
        except Exception:
            return []

        results = []
        for art in articles:
            title = art.get("title", "")
            desc = art.get("description", "") or ""
            combined = f"{title}. {desc}"
            label, score = self._vader_sentiment(combined)
            results.append({
                "title": title,
                "source": art.get("source", {}).get("name", "Unknown"),
                "url": art.get("url", ""),
                "published_at": art.get("publishedAt", ""),
                "sentiment": label,
                "sentiment_score": round(score, 4),
                "stock_symbols": [symbol],
                "summary": desc[:200],
            })
        return results

    def get_market_news(self) -> list[dict]:
        if not self._news_client:
            return []
        try:
            response = self._news_client.get_top_headlines(
                q="Indian stock market NSE BSE Nifty",
                language="en",
                page_size=15,
            )
            articles = response.get("articles", [])
        except Exception:
            return []

        results = []
        for art in articles:
            title = art.get("title", "")
            desc = art.get("description", "") or ""
            label, score = self._vader_sentiment(f"{title}. {desc}")
            results.append({
                "title": title,
                "source": art.get("source", {}).get("name", "Unknown"),
                "url": art.get("url", ""),
                "published_at": art.get("publishedAt", ""),
                "sentiment": label,
                "sentiment_score": round(score, 4),
                "stock_symbols": [],
                "summary": desc[:200],
            })
        return results

    def aggregate_sentiment(self, news_items: list[dict]) -> dict:
        if not news_items:
            return {"overall": "NEUTRAL", "score": 0.0, "positive": 0, "negative": 0, "neutral": 0}
        pos = sum(1 for n in news_items if n["sentiment"] == "POSITIVE")
        neg = sum(1 for n in news_items if n["sentiment"] == "NEGATIVE")
        neu = sum(1 for n in news_items if n["sentiment"] == "NEUTRAL")
        avg_score = sum(n["sentiment_score"] for n in news_items) / len(news_items)
        if avg_score >= 0.05:
            overall = "POSITIVE"
        elif avg_score <= -0.05:
            overall = "NEGATIVE"
        else:
            overall = "NEUTRAL"
        return {
            "overall": overall,
            "score": round(avg_score, 4),
            "positive": pos,
            "negative": neg,
            "neutral": neu,
        }
