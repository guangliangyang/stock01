# -*- coding: utf-8 -*-
"""Check AkShare function signatures."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import akshare as ak
import inspect

# Check stock_history_dividend_detail signature
print("stock_history_dividend_detail signature:")
try:
    sig = inspect.signature(ak.stock_history_dividend_detail)
    print(f"  Parameters: {sig}")
except Exception as e:
    print(f"  Error: {e}")

# Check stock_fhps_em signature
print("\nstock_fhps_em signature:")
try:
    sig = inspect.signature(ak.stock_fhps_em)
    print(f"  Parameters: {sig}")
except Exception as e:
    print(f"  Error: {e}")

# Check stock_individual_info_em signature
print("\nstock_individual_info_em signature:")
try:
    sig = inspect.signature(ak.stock_individual_info_em)
    print(f"  Parameters: {sig}")
except Exception as e:
    print(f"  Error: {e}")

# List available dividend-related functions
print("\nDividend-related functions in akshare:")
for name in dir(ak):
    if 'dividend' in name.lower() or 'fhps' in name.lower() or 'fh' in name.lower():
        print(f"  {name}")
