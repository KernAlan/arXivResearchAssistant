# src/output_manager.py
from datetime import datetime
import os
import git
from pathlib import Path

class DigestOutputManager:
    def __init__(self, base_dir="digests"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def save_digest(self, html_content):
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"arxiv_digest_{timestamp}.html"
        
        # Save the file
        filepath = self.base_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return filepath

    def commit_to_git(self, filepath):
        try:
            repo = git.Repo(search_parent_directories=True)
            repo.index.add([str(filepath)])
            repo.index.commit(f"Add arxiv digest for {datetime.now().strftime('%Y-%m-%d')}")
            print(f"Committed digest {filepath} to git repository")
        except git.InvalidGitRepositoryError:
            print("Not a git repository. Skipping commit.")