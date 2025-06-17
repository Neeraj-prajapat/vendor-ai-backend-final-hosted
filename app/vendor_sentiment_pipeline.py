import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup
from newsapi import NewsApiClient
from googleapiclient.discovery import build as build_google
import praw  # Reddit client
from transformers import pipeline
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -----------------------------
# Configuration / Credentials
# -----------------------------
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vendor_sentiment.db')

# -----------------------------
# Database Setup
# -----------------------------
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class SentimentRecord(Base):
    __tablename__ = 'sentiment_records'
    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String, index=True)
    source = Column(String)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    text = Column(Text)
    sentiment = Column(Float)
    summary = Column(Text)

Base.metadata.create_all(engine)

# -----------------------------
# Data Ingestion Clients
# -----------------------------
class NewsClient:
    def __init__(self, api_key: str):
        self.client = NewsApiClient(api_key=api_key)

    def fetch(self, vendor: str) -> List[Dict[str, Any]]:
        articles = self.client.get_everything(q=vendor, language='en', sort_by='publishedAt')
        return articles.get('articles', [])

class TrustpilotScraper:
    BASE_URL = "https://www.trustpilot.com/review/"

    def fetch(self, domain: str) -> List[str]:
        url = self.BASE_URL + domain
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        reviews = [tag.get_text(strip=True) for tag in soup.select('p.review-content')]
        return reviews

class GooglePlacesClient:
    def __init__(self, api_key: str):
        self.client = build_google('places', 'v1', developerKey=api_key)

    def fetch(self, place_id: str) -> List[str]:
        res = self.client.placeDetails(placeId=place_id).execute()
        return [r['text'] for r in res.get('result', {}).get('reviews', [])]

class RedditClient:
    def __init__(self, client_id, client_secret, user_agent):
        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  user_agent=user_agent)

    def fetch(self, subreddit: str, limit: int = 50) -> List[str]:
        posts = self.reddit.subreddit(subreddit).new(limit=limit)
        return [post.title + "\n" + post.selftext for post in posts]

# -----------------------------
# NLP Processing
# -----------------------------
class TextAnalyzer:
    def __init__(self):
        self.sentiment_pipeline = pipeline('sentiment-analysis')
        self.summarizer = pipeline('summarization')

    def analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        results = []
        for text in texts:
            try:
                sent = self.sentiment_pipeline(text[:512])[0]
                summary = self.summarizer(text, max_length=100, min_length=20)[0]['summary_text']
                score = sent['score'] if sent['label'] == 'POSITIVE' else -sent['score']
                results.append({'text': text, 'sentiment': score, 'summary': summary})
            except Exception as e:
                logging.error(f"Failed to analyze text: {e}")
        return results

# -----------------------------
# Aggregation & Storage
# -----------------------------
class Aggregator:
    def __init__(self, db_session):
        self.session = db_session

    def save(self, vendor: str, source: str, analysis: List[Dict[str, Any]]):
        for item in analysis:
            rec = SentimentRecord(
                vendor=vendor,
                source=source,
                text=item['text'],
                sentiment=item['sentiment'],
                summary=item['summary']
            )
            self.session.add(rec)
        self.session.commit()

# -----------------------------
# Orchestrator
# -----------------------------
class Pipeline:
    def __init__(self):
        self.news = NewsClient(NEWSAPI_KEY)
        self.tp = TrustpilotScraper()
        self.reddit = RedditClient(REDDIT_CLIENT_ID,
                                   REDDIT_CLIENT_SECRET,
                                   REDDIT_USER_AGENT)
        self.nlp = TextAnalyzer()
        self.session = SessionLocal()
        self.agg = Aggregator(self.session)

    def run_for_vendor(self, domain: str, subreddit: str = None, place_id: str = None):
        # News
        articles = [a['title'] + '\n' + a['description'] for a in self.news.fetch(domain)]
        news_analysis = self.nlp.analyze(articles)
        self.agg.save(domain, 'news', news_analysis)

        # Trustpilot
        try:
            reviews = self.tp.fetch(domain)
            tp_analysis = self.nlp.analyze(reviews)
            self.agg.save(domain, 'trustpilot', tp_analysis)
        except Exception:
            logging.warning("Failed Trustpilot for %s", domain)

        # Reddit
        if subreddit:
            posts = self.reddit.fetch(subreddit)
            rd_analysis = self.nlp.analyze(posts)
            self.agg.save(domain, f'reddit/{subreddit}', rd_analysis)

        # Google Places
        if place_id:
            greviews = self.news.fetch(domain)
            gp_analysis = self.nlp.analyze(greviews)
            self.agg.save(domain, 'google_places', gp_analysis)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pipeline = Pipeline()
    # Example: run for example.com
    pipeline.run_for_vendor('example.com', subreddit='example', place_id=None)  

    # For periodic execution, wrap this script in cron or APScheduler
