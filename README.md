# Dividend Stock Screener (股息价值选股系统)

A Windows desktop application for screening A-share stocks based on dividend yield criteria. Built with Python and PyQt5.

## Features

- **Stock Screening**: Filter stocks by listing years, consecutive dividend years, and average yield
- **Triple Data Sources**: Yahoo Finance (global), AkShare, and Baostock with automatic fallback
- **Global Accessibility**: Yahoo Finance as default for users outside China
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
   - **Min Avg Yield**: Minimum average dividend yield (%) calculated over the dividend years

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
- 中文 (Chinese) - Default

Changes apply immediately without restart.

### Data Source Selection

Use the **Data Source** dropdown in the toolbar:
- **Auto (Fallback)**: Yahoo Finance → AkShare → Baostock
- **AkShare**: Chinese data source (best in China)
- **Baostock**: Chinese backup source
- **Yahoo Finance**: Global accessibility (best outside China)

## Project Structure

```
stock01/
├── src/
│   ├── core/                 # Business logic
│   │   ├── alert_engine.py   # Sell alert detection
│   │   ├── dividend_calculator.py
│   │   └── stock_screener.py
│   ├── data/                 # Data sources
│   │   ├── akshare_client.py       # Chinese data source
│   │   ├── baostock_client.py      # Chinese backup source
│   │   ├── yahoo_finance_client.py # Global data source
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
| `min_avg_yield` | 5.0 | Minimum average yield (%) over dividend years |
| `sell_threshold` | 3.0 | Sell alert threshold (%) |
| `data_source` | auto | Data source: auto, akshare, baostock, yahoo_finance |
| `language` | zh | UI language: en, zh |

## Data Sources

### Yahoo Finance (Default for individual stocks)
- Global accessibility (works outside China)
- A-share data via `.SS` (Shanghai) and `.SZ` (Shenzhen) suffixes
- Good for international users

### AkShare
- Real-time A-share data
- Comprehensive dividend history
- Best choice within China
- May have rate limiting

### Baostock
- Free historical data
- Reliable fallback option
- Requires login (handled automatically)

### Auto Mode Behavior
- **Stock list**: AkShare → Baostock (Chinese sources only)
- **Individual stock data**: Yahoo Finance → AkShare → Baostock

This prioritizes global accessibility while ensuring comprehensive stock coverage.

## Dependencies

- **PyQt5**: Desktop UI framework
- **yfinance**: Yahoo Finance data (global)
- **akshare**: A-share market data (China)
- **baostock**: Backup data source (China)
- **pandas**: Data manipulation
- **pydantic**: Data validation
- **loguru**: Logging
- **winotify**: Windows toast notifications

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
