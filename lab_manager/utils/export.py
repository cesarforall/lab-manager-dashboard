# utils/export.py
import pandas as pd
from pathlib import Path
import datetime

def export_to_excel(data: list[dict], file_path=None):
    if not data or not file_path:
        return None

    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return file_path