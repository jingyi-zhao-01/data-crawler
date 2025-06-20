"""
News crawler for hardware launches, supply constraints, and energy market news
"""
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

from crawler.schema import HardwareNewsModel, EnergyMarketEventModel, NewsSourceData

load_dotenv()


class NewsCrawler:
    def __init__(self):
        self.rss_feeds = NewsSourceData.rss_feeds
        self.keywords = NewsSourceData.keywords
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; DataCrawler/1.0; +http://example.com/contact)'
        }

    async def fetch_rss_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        articles = []
                        for entry in feed.entries:
                            article = {
                                'title': entry.get('title', ''),
                                'link': entry.get('link', ''),
                                'description': entry.get('description', ''),
                                'published': entry.get('published', ''),
                                'source': feed_url
                            }
                            articles.append(article)
                        
                        return articles
                    else:
                        print(f"Error fetching RSS feed {feed_url}: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error in fetch_rss_feed for {feed_url}: {e}")
            return []

    async def fetch_article_content(self, url: str) -> Optional[str]:
        """Fetch full article content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text content
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return text
                    else:
                        return None
                        
        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
            return None

    def is_relevant_article(self, title: str, description: str) -> bool:
        """Check if article is relevant based on keywords"""
        content = f"{title} {description}".lower()
        return any(keyword.lower() in content for keyword in self.keywords)

    def extract_hardware_info(self, title: str, content: str) -> Dict[str, Any]:
        """Extract hardware-specific information from article"""
        hardware_info = {
            "hardware_type": None,
            "launch_date": None,
            "supply_status": None
        }
        
        # Detect hardware type
        if any(term in content.lower() for term in ["nvidia", "rtx", "gtx", "tesla", "a100", "h100"]):
            hardware_info["hardware_type"] = "NVIDIA"
        elif any(term in content.lower() for term in ["amd", "radeon", "instinct"]):
            hardware_info["hardware_type"] = "AMD"
        elif any(term in content.lower() for term in ["intel", "arc", "xe"]):
            hardware_info["hardware_type"] = "Intel"
        
        # Extract launch date
        date_patterns = [
            r"launch(?:ed|ing)?\s+(?:in\s+)?([a-zA-Z]+\s+\d{4})",
            r"available\s+(?:in\s+)?([a-zA-Z]+\s+\d{4})",
            r"release(?:d|ing)?\s+(?:in\s+)?([a-zA-Z]+\s+\d{4})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Parse date (simplified)
                    hardware_info["launch_date"] = datetime.strptime(date_str, "%B %Y")
                    break
                except:
                    continue
        
        # Extract supply status
        supply_indicators = {
            "shortage": ["shortage", "supply constraint", "limited availability", "out of stock"],
            "abundant": ["widely available", "in stock", "ample supply"],
            "delayed": ["delayed", "postponed", "pushed back"]
        }
        
        content_lower = content.lower()
        for status, indicators in supply_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                hardware_info["supply_status"] = status
                break
        
        return hardware_info

    def extract_energy_event_info(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """Extract energy market event information"""
        energy_keywords = ["storm", "hurricane", "power outage", "grid", "natural gas", "electricity", 
                          "energy crisis", "blackout", "pipeline", "refinery"]
        
        content_lower = content.lower()
        if not any(keyword in content_lower for keyword in energy_keywords):
            return None
        
        event_info = {
            "event_type": "unknown",
            "impact_level": "medium",
            "affected_regions": []
        }
        
        # Determine event type
        if any(term in content_lower for term in ["storm", "hurricane", "tornado"]):
            event_info["event_type"] = "weather"
        elif any(term in content_lower for term in ["geopolitical", "war", "sanctions"]):
            event_info["event_type"] = "geopolitical"
        elif any(term in content_lower for term in ["outage", "blackout", "grid failure"]):
            event_info["event_type"] = "infrastructure"
        
        # Determine impact level
        if any(term in content_lower for term in ["major", "severe", "critical", "emergency"]):
            event_info["impact_level"] = "high"
        elif any(term in content_lower for term in ["minor", "small", "limited"]):
            event_info["impact_level"] = "low"
        
        # Extract regions (simplified)
        regions = ["texas", "california", "new york", "florida", "midwest", "northeast", "southeast", "west coast"]
        for region in regions:
            if region in content_lower:
                event_info["affected_regions"].append(region.title())
        
        return event_info

    async def get_hardware_news(self, days_back: int = 7) -> List[HardwareNewsModel]:
        """Get hardware-related news"""
        try:
            all_articles = []
            
            # Fetch from all RSS feeds
            tasks = [self.fetch_rss_feed(feed) for feed in self.rss_feeds]
            feed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for articles in feed_results:
                if not isinstance(articles, Exception):
                    all_articles.extend(articles)
            
            # Filter relevant articles
            relevant_articles = [
                article for article in all_articles 
                if self.is_relevant_article(article['title'], article['description'])
            ]
            
            # Process articles
            hardware_news = []
            for article in relevant_articles[:20]:  # Limit to 20 articles
                try:
                    # Fetch full content
                    full_content = await self.fetch_article_content(article['link'])
                    if not full_content:
                        full_content = article['description']
                    
                    # Extract hardware information
                    hardware_info = self.extract_hardware_info(article['title'], full_content)
                    
                    if hardware_info["hardware_type"]:  # Only include if hardware type detected
                        news_model = HardwareNewsModel(
                            source=f"news_rss_{article['source']}",
                            title=article['title'],
                            content=full_content[:1000],  # Limit content length
                            **hardware_info
                        )
                        hardware_news.append(news_model)
                        
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
            
            return hardware_news
            
        except Exception as e:
            print(f"Error in get_hardware_news: {e}")
            return []

    async def get_energy_market_events(self, days_back: int = 7) -> List[EnergyMarketEventModel]:
        """Get energy market event news"""
        try:
            all_articles = []
            
            # Fetch from all RSS feeds
            tasks = [self.fetch_rss_feed(feed) for feed in self.rss_feeds]
            feed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for articles in feed_results:
                if not isinstance(articles, Exception):
                    all_articles.extend(articles)
            
            # Process articles for energy events
            energy_events = []
            for article in all_articles[:50]:  # Check more articles for energy events
                try:
                    # Fetch full content
                    full_content = await self.fetch_article_content(article['link'])
                    if not full_content:
                        full_content = article['description']
                    
                    # Extract energy event information
                    event_info = self.extract_energy_event_info(article['title'], full_content)
                    
                    if event_info:  # Only include if energy event detected
                        event_model = EnergyMarketEventModel(
                            source=f"news_rss_{article['source']}",
                            description=f"{article['title']}: {full_content[:500]}",
                            **event_info
                        )
                        energy_events.append(event_model)
                        
                except Exception as e:
                    print(f"Error processing energy article: {e}")
                    continue
            
            return energy_events
            
        except Exception as e:
            print(f"Error in get_energy_market_events: {e}")
            return []

    async def get_all_news(self) -> Dict[str, List[Any]]:
        """Get all news data"""
        tasks = [
            self.get_hardware_news(),
            self.get_energy_market_events()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "hardware_news": results[0] if not isinstance(results[0], Exception) else [],
            "energy_events": results[1] if not isinstance(results[1], Exception) else []
        }


async def main():
    """Test the news crawler"""
    crawler = NewsCrawler()
    news_data = await crawler.get_all_news()
    
    print("Hardware News:")
    for item in news_data["hardware_news"]:
        print(f"  {item.title} - {item.hardware_type}")
    
    print("\nEnergy Market Events:")
    for item in news_data["energy_events"]:
        print(f"  {item.event_type} - {item.impact_level}")


if __name__ == "__main__":
    asyncio.run(main())