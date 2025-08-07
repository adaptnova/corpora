#!/usr/bin/env python3
"""
Nova NLM Pipeline Monitoring Dashboard
Real-time monitoring of data ingestion and processing
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

class PipelineDashboard:
    def __init__(self):
        self.base_path = Path("/home/x/data/corpora")
        self.staging_path = self.base_path / "pipeline_staging"
        self.project_path = self.base_path / ".claude/projects/nlm-alpha"
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def format_bytes(self, bytes):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"
    
    def load_inventory(self):
        """Load corpus inventory"""
        inventory_file = self.project_path / "corpus_inventory.json"
        if inventory_file.exists():
            with open(inventory_file) as f:
                return json.load(f)
        return None
    
    def load_ingestion_stats(self):
        """Load ingestion statistics"""
        stats_file = self.staging_path / "ingestion_stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                return json.load(f)
        return None
    
    def count_staging_files(self):
        """Count files in staging"""
        counts = {}
        for subdir in ["raw", "metadata", "queue", "processed"]:
            path = self.staging_path / subdir
            if path.exists():
                counts[subdir] = len(list(path.glob("*")))
            else:
                counts[subdir] = 0
        return counts
    
    def calculate_ingestion_rate(self, stats):
        """Calculate ingestion rate"""
        if not stats or "engine" not in stats:
            return 0, 0
        
        engine = stats["engine"]
        start = datetime.fromisoformat(engine.get("session_start", datetime.now().isoformat()))
        elapsed = (datetime.now() - start).total_seconds()
        
        if elapsed > 0:
            items_per_hour = (engine.get("items_processed", 0) / elapsed) * 3600
            return items_per_hour, elapsed
        return 0, 0
    
    def display_dashboard(self):
        """Display monitoring dashboard"""
        self.clear_screen()
        
        # Header
        print("="*80)
        print("                    NOVA NLM PIPELINE MONITORING DASHBOARD")
        print("="*80)
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Load data
        inventory = self.load_inventory()
        ingestion_stats = self.load_ingestion_stats()
        staging_counts = self.count_staging_files()
        
        # Corpus Overview
        print("📊 CORPUS OVERVIEW")
        print("-"*40)
        if inventory:
            summary = inventory.get("summary", {})
            print(f"Total Size:        {summary.get('total_size_gb', 0):.2f} GB")
            print(f"Total Files:       {summary.get('total_files', 0):,}")
            print(f"Compressed:        {summary.get('compressed_archives_count', 0)} archives ({summary.get('compressed_size_gb', 0):.2f} GB)")
            print()
            
            # Categories
            print("Categories:")
            for cat, data in summary.get("categories", {}).items():
                print(f"  {cat:20} {data['files']:6,} files  {data['size_gb']:8.2f} GB")
        else:
            print("No inventory data available")
        print()
        
        # Ingestion Status
        print("🔄 INGESTION STATUS")
        print("-"*40)
        if ingestion_stats:
            engine = ingestion_stats.get("engine", {})
            print(f"Session Start:     {engine.get('session_start', 'N/A')}")
            print(f"Items Processed:   {engine.get('items_processed', 0):,}")
            print(f"Items Queued:      {engine.get('items_queued', 0):,}")
            print(f"Duplicates:        {engine.get('duplicates_skipped', 0):,}")
            
            # Calculate rate
            rate, elapsed = self.calculate_ingestion_rate(ingestion_stats)
            print(f"Ingestion Rate:    {rate:.1f} items/hour")
            print(f"Uptime:           {timedelta(seconds=int(elapsed))}")
            print()
            
            # Source stats
            print("Source Statistics:")
            for source, stats in ingestion_stats.get("sources", {}).items():
                print(f"  {source:12} - {stats.get('items_fetched', 0):4} items, {stats.get('errors', 0)} errors")
        else:
            print("No ingestion data available")
        print()
        
        # Staging Area
        print("📁 STAGING AREA")
        print("-"*40)
        print(f"Metadata:     {staging_counts.get('metadata', 0):6,} files")
        print(f"Raw Data:     {staging_counts.get('raw', 0):6,} files")
        print(f"Queue:        {staging_counts.get('queue', 0):6,} files")
        print(f"Processed:    {staging_counts.get('processed', 0):6,} files")
        print()
        
        # Target Progress
        print("🎯 WEEK 1 TARGET PROGRESS")
        print("-"*40)
        target_gb = 25
        current_gb = inventory.get("summary", {}).get("total_size_gb", 0) if inventory else 0
        progress = (current_gb / target_gb) * 100
        
        # Progress bar
        bar_length = 40
        filled = int(bar_length * current_gb / target_gb)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"Progress: [{bar}] {progress:.1f}%")
        print(f"Current: {current_gb:.2f} GB / Target: {target_gb} GB")
        
        days_elapsed = 0  # Will calculate from project start
        days_remaining = 7 - days_elapsed
        if days_remaining > 0:
            needed_per_day = (target_gb - current_gb) / days_remaining
            print(f"Need: {needed_per_day:.2f} GB/day for next {days_remaining} days")
        print()
        
        # System Health
        print("💚 SYSTEM HEALTH")
        print("-"*40)
        
        # Check if ingestion is running
        if ingestion_stats:
            last_update = datetime.fromisoformat(
                ingestion_stats.get("engine", {}).get("session_start", datetime.now().isoformat())
            )
            if (datetime.now() - last_update) < timedelta(minutes=10):
                print("✅ Ingestion:     RUNNING")
            else:
                print("⚠️  Ingestion:     STALE (>10 min)")
        else:
            print("❌ Ingestion:     NOT RUNNING")
        
        # Check staging
        if staging_counts.get("metadata", 0) > 0:
            print("✅ Staging:       ACTIVE")
        else:
            print("⚠️  Staging:       EMPTY")
        
        # Check for errors
        total_errors = 0
        if ingestion_stats:
            for source, stats in ingestion_stats.get("sources", {}).items():
                total_errors += stats.get("errors", 0)
        
        if total_errors == 0:
            print("✅ Errors:        NONE")
        else:
            print(f"⚠️  Errors:        {total_errors} total")
        
        print()
        print("="*80)
        print("Press Ctrl+C to exit")
    
    def run(self, refresh_interval=5):
        """Run dashboard with auto-refresh"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard stopped")

if __name__ == "__main__":
    dashboard = PipelineDashboard()
    
    # Display once for testing
    dashboard.display_dashboard()
    
    # Uncomment to run with auto-refresh
    # dashboard.run(refresh_interval=5)