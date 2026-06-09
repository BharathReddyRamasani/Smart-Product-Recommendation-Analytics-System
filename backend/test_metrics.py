import sys
import os
import asyncio

# Setup FastAPI context
from app.utils.database import connect_to_mongo, close_mongo
from app.ml.engine import ml_engine

def run_metrics():
    db = connect_to_mongo()
    try:
        print("Fitting ml_engine with current DB...")
        ml_engine.fit(db)
        print("Fetching metrics...")
        metrics = ml_engine.get_metrics(k=10)
        print("Metrics:", metrics)
    finally:
        close_mongo()

if __name__ == "__main__":
    run_metrics()
