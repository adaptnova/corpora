#!/usr/bin/env python3
"""
DVC Data Version Control Manager
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

class DVCManager:
    def __init__(self, repo_path='.'):
        self.repo_path = Path(repo_path)
        self.dvc_dir = self.repo_path / '.dvc'
        
    def init(self):
        """Initialize DVC in repo"""
        if not self.dvc_dir.exists():
            subprocess.run(['dvc', 'init'], cwd=self.repo_path)
            print("✅ DVC initialized")
        else:
            print("DVC already initialized")
    
    def add_data_dir(self, data_dir='data'):
        """Add data directory to DVC tracking"""
        subprocess.run(['dvc', 'add', data_dir], cwd=self.repo_path)
        subprocess.run(['git', 'add', f'{data_dir}.dvc', '.gitignore'], cwd=self.repo_path)
        print(f"✅ Added {data_dir} to DVC tracking")
    
    def create_pipeline(self):
        """Create DVC pipeline stages"""
        pipeline = {
            'stages': {
                'ingest': {
                    'cmd': 'python -m pipeline.ingestion.engine',
                    'deps': [
                        'pipeline/ingestion/engine.py',
                        'configs/sources.yaml'
                    ],
                    'outs': [
                        'data/raw'
                    ]
                },
                'process': {
                    'cmd': 'python -m pipeline.processing.cleaner',
                    'deps': [
                        'pipeline/processing/cleaner.py',
                        'data/raw'
                    ],
                    'outs': [
                        'data/processed'
                    ]
                },
                'stage': {
                    'cmd': 'python -m pipeline.staging.prepare',
                    'deps': [
                        'data/processed'
                    ],
                    'outs': [
                        'data/staged'
                    ]
                }
            }
        }
        
        with open(self.repo_path / 'dvc.yaml', 'w') as f:
            import yaml
            yaml.dump(pipeline, f)
        
        print("✅ DVC pipeline created")
    
    def push(self, remote='origin'):
        """Push data to remote storage"""
        subprocess.run(['dvc', 'push', '-r', remote], cwd=self.repo_path)
        print(f"✅ Data pushed to {remote}")
    
    def pull(self, remote='origin'):
        """Pull data from remote storage"""
        subprocess.run(['dvc', 'pull', '-r', remote], cwd=self.repo_path)
        print(f"✅ Data pulled from {remote}")
    
    def commit_version(self, message):
        """Commit data version"""
        # Add changes
        subprocess.run(['dvc', 'add', 'data'], cwd=self.repo_path)
        subprocess.run(['git', 'add', 'data.dvc'], cwd=self.repo_path)
        
        # Commit
        timestamp = datetime.now().isoformat()
        full_message = f"{message}\n\nTimestamp: {timestamp}"
        subprocess.run(['git', 'commit', '-m', full_message], cwd=self.repo_path)
        
        print(f"✅ Version committed: {message}")
    
    def status(self):
        """Check DVC status"""
        result = subprocess.run(['dvc', 'status'], cwd=self.repo_path, capture_output=True, text=True)
        return result.stdout

if __name__ == "__main__":
    manager = DVCManager()
    manager.init()
    print("DVC manager ready")