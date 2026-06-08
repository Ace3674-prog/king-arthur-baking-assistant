import json
import os
import pandas as pd

from scraper.config import OUTPUT_JSON, OUTPUT_CSV


def ensure_output_directory(path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def save_json(data):
    ensure_output_directory(OUTPUT_JSON)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def save_csv(data):
    ensure_output_directory(OUTPUT_CSV)
    df = pd.DataFrame(data)
    df.to_csv(OUTPUT_CSV, index=False)
