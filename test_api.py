# -*- coding: utf-8 -*-
"""Quick test script for AkShare API."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import akshare as ak
import pandas as pd

print("Testing AkShare API...")

# Test 1: Get stock info for a known stock (Kweichow Moutai)
print("\n1. Testing stock_individual_info_em (600519 - Moutai)...")
try:
    time.sleep(1)
    df = ak.stock_individual_info_em(symbol="600519")
    print(df.to_string())
    print("OK!")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Get dividend history with correct parameter name (symbol)
print("\n2. Testing stock_history_dividend_detail (600519)...")
try:
    time.sleep(1)
    df = ak.stock_history_dividend_detail(symbol="600519", indicator="分红", date="")
    print(df.head().to_string())
    print(f"Total dividend records: {len(df)}")
    print("OK!")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Get current price
print("\n3. Testing stock_zh_a_spot_em (real-time quotes)...")
try:
    time.sleep(1)
    df = ak.stock_zh_a_spot_em()
    moutai = df[df["代码"] == "600519"]
    print(moutai[["代码", "名称", "最新价", "涨跌幅"]].to_string())
    print("OK!")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Get historical prices
print("\n4. Testing stock_zh_a_hist (600519)...")
try:
    time.sleep(1)
    df = ak.stock_zh_a_hist(symbol="600519", period="daily", start_date="20240101", end_date="20240131", adjust="qfq")
    print(df.head().to_string())
    print("OK!")
except Exception as e:
    print(f"Error: {e}")

print("\n=== All tests complete ===")
