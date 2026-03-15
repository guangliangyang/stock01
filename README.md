# Dividend Stock Screener (股息价值选股系统)

A Windows desktop application for screening A-share stocks based on dividend yield criteria. Built with Python and PyQt5.

## Features

- **Stock Screening**: Filter stocks by listing years, consecutive dividend years, and 5-year average yield
- **Dual Data Sources**: AkShare (primary) with automatic fallback to Baostock
- **Portfolio Management**: Track your holdings and monitor sell alerts
- **Sell Alerts**: Get notified when stock yields drop below your threshold
- **Bilingual UI**: Switch between English and Chinese (中文) at runtime
- **Windows Notifications**: Toast notifications for alerts and screening completion
- **Log Viewer**: Real-time colored log viewer with filtering and export
- **CSV Export**: Export screening results for further analysis

## Screenshots

| English | Chinese |
|---------|---------|
| Screening Results | 筛选结果 |
| Portfolio Management | 持仓管理 |

## Installation

### Prerequisites

- Python 3.10+
- Windows 10/11

### Setup

```bash
# Clone the repository
git clone https://github.com/guangliangyang/stock01.git
cd stock01

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run from Source

```bash
python src/main.py
```

### Build Executable

```bash
pip install pyinstaller
pyinstaller app.spec --clean
```

The executable will be created at `dist/DividendStockScreener.exe`.

## Usage

### Stock Screening

1. Configure buy criteria in the left panel:
   - **Min Listing Years**: Minimum years since IPO
   - **Min Dividend Years**: Minimum consecutive years of dividend payments
   - **Min 5Y Avg Yield**: Minimum 5-year average dividend yield (%)

2. Click **Scan Stocks** to start screening all A-share stocks

3. Results appear in the table, sortable by any column

4. Export results to CSV or add stocks to your portfolio

### Portfolio Management

1. Switch to the **My Portfolio** tab

2. Add stocks manually or from screening results

3. Set **Sell Threshold** in the config panel

4. Click **Check Alerts** to check for stocks with yields below threshold

5. Receive Windows toast notifications for sell alerts

### Language Switching

Use the **Language** dropdown in the toolbar to switch between:
- English
- 中文 (Chinese)

Changes apply immediately without restart.

## Project Structure

```
stock01/
├── src/
│   ├── core/                 # Business logic
│   │   ├── alert_engine.py   # Sell alert detection
│   │   ├── dividend_calculator.py
│   │   └── stock_screener.py
│   ├── data/                 # Data sources
│   │   ├── akshare_client.py # Primary data source
│   │   ├── baostock_client.py # Backup data source
│   │   └── stock_repository.py
│   ├── i18n/                 # Internationalization
│   │   ├── locales/
│   │   │   ├── en.json
│   │   │   └── zh.json
│   │   └── translator.py
│   ├── models/               # Data models
│   ├── notification/         # Windows toast notifications
│   ├── persistence/          # Settings & portfolio storage
│   ├── ui/                   # PyQt5 UI
│   │   └── widgets/
│   └── main.py               # Entry point
├── config/
│   └── default_settings.json
├── app.spec                  # PyInstaller config
└── requirements.txt
```

## Configuration

Settings are stored in `data/settings.json` and include:

| Setting | Default | Description |
|---------|---------|-------------|
| `min_listing_years` | 10 | Minimum years since IPO |
| `min_dividend_years` | 5 | Minimum consecutive dividend years |
| `min_avg_yield` | 3.0 | Minimum 5-year average yield (%) |
| `sell_threshold` | 2.5 | Sell alert threshold (%) |
| `data_source` | auto | Data source: auto, akshare, baostock |
| `language` | en | UI language: en, zh |

## Data Sources

### AkShare (Primary)
- Real-time A-share data
- Comprehensive dividend history
- May have rate limiting

### Baostock (Backup)
- Free historical data
- Reliable fallback option
- Requires login (handled automatically)

The app automatically switches to Baostock if AkShare fails.

## Dependencies

- **PyQt5**: Desktop UI framework
- **akshare**: A-share market data
- **baostock**: Backup data source
- **pandas**: Data manipulation
- **pydantic**: Data validation
- **loguru**: Logging
- **winotify**: Windows toast notifications

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
