"""Configuration management for ArxivDigest"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class Config:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = "config.yaml"):
        """Load configuration from YAML file"""
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)
    
    @property
    def system(self) -> Dict[str, Any]:
        """Get system configuration"""
        return self._config["system"]
    
    @property
    def user(self) -> Dict[str, Any]:
        """Get user configuration"""
        return self._config["user"]
    
    @property
    def model(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self._config["model"]
    
    def get_topic_abbreviation(self, topic: str) -> str:
        """Get arXiv abbreviation for topic"""
        if topic == "Physics":
            raise ValueError("Must specify a physics subtopic")
        elif topic in self.system["physics_subtopics"]:
            return self.system["physics_subtopics"][topic]
        elif topic in self.system["arxiv_topics"]:
            return self.system["arxiv_topics"][topic]
        else:
            raise ValueError(f"Invalid topic: {topic}")
    
    def validate(self) -> bool:
        """Validate configuration"""
        required_keys = ["system", "user", "model"]
        return all(key in self._config for key in required_keys)

# Global config instance
config = Config() 