#!/usr/bin/env python3
"""
Nova NLM Data Ingestion Engine
24/7 continuous data acquisition from multiple sources
"""

import os
import json
import time
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from queue import Queue
from threading import Thread, Lock
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

class DataSource:
    """Base class for data sources"""
    def __init__(self, name, rate_limit=1.0):
        self.name = name
        self.rate_limit = rate_limit  # seconds between requests
        self.last_request = 0
        self.stats = {
            "items_fetched": 0,
            "bytes_downloaded": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
    
    def respect_rate_limit(self):
        """Enforce polite crawling"""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()
    
    def fetch(self):
        """Override in subclasses"""
        raise NotImplementedError

class GitHubSource(DataSource):
    """GitHub repository crawler"""
    def __init__(self, token=None):
        super().__init__("github", rate_limit=2.0)
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        self.base_url = "https://api.github.com"
        
    def fetch_trending(self, language="python", since="daily"):
        """Fetch trending repositories"""
        self.respect_rate_limit()
        
        # Using GitHub's search API for most starred recent repos
        query = f"language:{language} created:>2024-01-01 sort:stars"
        url = f"{self.base_url}/search/repositories?q={query}&per_page=30"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                repos = []
                for repo in data.get("items", []):
                    repos.append({
                        "type": "github_repo",
                        "url": repo["html_url"],
                        "name": repo["full_name"],
                        "stars": repo["stargazers_count"],
                        "language": repo.get("language"),
                        "description": repo.get("description"),
                        "clone_url": repo["clone_url"],
                        "fetched_at": datetime.now().isoformat()
                    })
                self.stats["items_fetched"] += len(repos)
                return repos
            else:
                self.stats["errors"] += 1
                return []
        except Exception as e:
            print(f"GitHub fetch error: {e}")
            self.stats["errors"] += 1
            return []

class ArXivSource(DataSource):
    """ArXiv paper crawler"""
    def __init__(self):
        super().__init__("arxiv", rate_limit=3.0)
        self.base_url = "http://export.arxiv.org/api/query"
        self.categories = ["cs.AI", "cs.LG", "cs.CL", "cs.DC"]  # AI, ML, CompLang, Distributed
        
    def fetch_recent(self, max_results=50):
        """Fetch recent papers from target categories"""
        self.respect_rate_limit()
        
        papers = []
        for category in self.categories:
            try:
                query = f"cat:{category}"
                url = f"{self.base_url}?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
                
                response = requests.get(url)
                if response.status_code == 200:
                    # Parse XML manually
                    root = ET.fromstring(response.content)
                    
                    # Define namespaces
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    
                    entries = root.findall('atom:entry', ns)
                    for entry in entries:
                        title = entry.find('atom:title', ns).text if entry.find('atom:title', ns) is not None else ""
                        summary = entry.find('atom:summary', ns).text if entry.find('atom:summary', ns) is not None else ""
                        
                        # Get PDF link
                        pdf_link = ""
                        for link in entry.findall('atom:link', ns):
                            if link.get('type') == 'application/pdf':
                                pdf_link = link.get('href')
                                break
                        
                        # Get authors
                        authors = []
                        for author in entry.findall('atom:author', ns):
                            name = author.find('atom:name', ns)
                            if name is not None:
                                authors.append(name.text)
                        
                        papers.append({
                            "type": "arxiv_paper",
                            "title": title.strip(),
                            "authors": authors,
                            "abstract": summary.strip(),
                            "pdf_url": pdf_link,
                            "category": category,
                            "fetched_at": datetime.now().isoformat()
                        })
                    
                    self.stats["items_fetched"] += len(entries)
            except Exception as e:
                print(f"ArXiv fetch error for {category}: {e}")
                self.stats["errors"] += 1
                
        return papers

class HackerNewsSource(DataSource):
    """HackerNews crawler"""
    def __init__(self):
        super().__init__("hackernews", rate_limit=1.0)
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        
    def fetch_top_stories(self, limit=30):
        """Fetch top HN stories with comments"""
        self.respect_rate_limit()
        
        try:
            # Get top story IDs
            response = requests.get(f"{self.base_url}/topstories.json")
            if response.status_code != 200:
                return []
                
            story_ids = response.json()[:limit]
            stories = []
            
            for story_id in story_ids:
                self.respect_rate_limit()
                
                # Get story details
                story_response = requests.get(f"{self.base_url}/item/{story_id}.json")
                if story_response.status_code == 200:
                    story = story_response.json()
                    if story and story.get("type") == "story":
                        stories.append({
                            "type": "hn_story",
                            "id": story_id,
                            "title": story.get("title"),
                            "url": story.get("url"),
                            "score": story.get("score"),
                            "by": story.get("by"),
                            "time": story.get("time"),
                            "descendants": story.get("descendants", 0),
                            "text": story.get("text"),
                            "fetched_at": datetime.now().isoformat()
                        })
                        
            self.stats["items_fetched"] += len(stories)
            return stories
            
        except Exception as e:
            print(f"HackerNews fetch error: {e}")
            self.stats["errors"] += 1
            return []

class IngestionEngine:
    """Main ingestion orchestrator"""
    def __init__(self, output_dir="/home/x/data/corpora/pipeline_staging"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create staging directories
        for subdir in ["raw", "metadata", "queue", "processed"]:
            (self.output_dir / subdir).mkdir(exist_ok=True)
        
        # Initialize sources
        self.sources = {
            "github": GitHubSource(),
            "arxiv": ArXivSource(),
            "hackernews": HackerNewsSource()
        }
        
        # Processing queue
        self.queue = Queue()
        self.processed_hashes = set()
        self.lock = Lock()
        
        # Load previous hashes if exists
        self.hash_file = self.output_dir / "processed_hashes.json"
        if self.hash_file.exists():
            with open(self.hash_file) as f:
                self.processed_hashes = set(json.load(f))
        
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "items_queued": 0,
            "items_processed": 0,
            "duplicates_skipped": 0,
            "bytes_downloaded": 0
        }
    
    def generate_hash(self, item):
        """Generate unique hash for deduplication"""
        # Create hash from key fields
        key_str = ""
        if item["type"] == "github_repo":
            key_str = item["url"]
        elif item["type"] == "arxiv_paper":
            key_str = item["pdf_url"]
        elif item["type"] == "hn_story":
            key_str = str(item["id"])
        else:
            key_str = json.dumps(item, sort_keys=True)
            
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def save_item(self, item):
        """Save item to staging area"""
        item_hash = self.generate_hash(item)
        
        # Check for duplicates
        if item_hash in self.processed_hashes:
            self.stats["duplicates_skipped"] += 1
            return False
        
        # Save metadata
        metadata_path = self.output_dir / "metadata" / f"{item_hash}.json"
        with open(metadata_path, 'w') as f:
            json.dump(item, f, indent=2)
        
        # Add to processed set
        with self.lock:
            self.processed_hashes.add(item_hash)
            self.stats["items_processed"] += 1
        
        # Queue for download if has URL
        if item.get("url") or item.get("pdf_url") or item.get("clone_url"):
            self.queue.put(item)
        
        return True
    
    def fetch_all_sources(self):
        """Fetch from all configured sources"""
        all_items = []
        
        print("\n" + "="*60)
        print(f"INGESTION CYCLE - {datetime.now().isoformat()}")
        print("="*60)
        
        # GitHub
        print("Fetching from GitHub...")
        github_items = self.sources["github"].fetch_trending()
        all_items.extend(github_items)
        print(f"  → {len(github_items)} repos found")
        
        # ArXiv
        print("Fetching from ArXiv...")
        arxiv_items = self.sources["arxiv"].fetch_recent(max_results=20)
        all_items.extend(arxiv_items)
        print(f"  → {len(arxiv_items)} papers found")
        
        # HackerNews
        print("Fetching from HackerNews...")
        hn_items = self.sources["hackernews"].fetch_top_stories(limit=20)
        all_items.extend(hn_items)
        print(f"  → {len(hn_items)} stories found")
        
        # Process items
        new_items = 0
        for item in all_items:
            if self.save_item(item):
                new_items += 1
        
        print(f"\nResults: {new_items} new items, {self.stats['duplicates_skipped']} duplicates skipped")
        
        # Save hashes
        with open(self.hash_file, 'w') as f:
            json.dump(list(self.processed_hashes), f)
        
        return new_items
    
    def run_continuous(self, interval=300):
        """Run continuous ingestion (default 5 minutes)"""
        print(f"\n🚀 Starting continuous ingestion (interval: {interval}s)")
        
        while True:
            try:
                self.fetch_all_sources()
                
                # Save stats
                stats_file = self.output_dir / "ingestion_stats.json"
                with open(stats_file, 'w') as f:
                    combined_stats = {
                        "engine": self.stats,
                        "sources": {
                            name: source.stats 
                            for name, source in self.sources.items()
                        }
                    }
                    json.dump(combined_stats, f, indent=2)
                
                print(f"\nNext cycle in {interval} seconds...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n⛔ Ingestion stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in ingestion cycle: {e}")
                time.sleep(30)  # Wait 30s on error

if __name__ == "__main__":
    engine = IngestionEngine()
    
    # Run one cycle for testing
    print("\n🔍 Running single ingestion cycle for testing...")
    new_items = engine.fetch_all_sources()
    
    print(f"\n✅ Test cycle complete: {new_items} new items")
    print(f"   Staging dir: {engine.output_dir}")
    
    # Uncomment to run continuously
    # engine.run_continuous(interval=300)