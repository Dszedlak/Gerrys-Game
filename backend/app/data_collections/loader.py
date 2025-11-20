# app/data_collections/loader.py
import json
from pathlib import Path

def load_governments():
    path = Path(__file__).parent / "governments.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_jobs():
    path = Path(__file__).parent / "jobs.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
    
def get_collections():
    return {
        "governments": load_governments(),
        "jobs": load_jobs()
    }