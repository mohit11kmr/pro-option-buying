# Nifty Options Trading Toolkit

This repository contains tools for analyzing and backtesting trading strategies on NIFTY options data, integrating with the SmartAPI, generating synthetic historical market data, and incorporating basic AI/ML signals.

## 📦 Project Structure

- `src/` - primary application code
  - `utils/` - helper utilities such as market data processing, backtester, AI integration
  - `utils/ml/` - machine learning modules (pattern recognition, price prediction, sentiment analysis, signal generation)
  - `trading/` - strategy definitions and execution logic
  - `web/` - web interface components (if any)
- `smartapi-python/` - vendored SmartAPI client/library
- `data/` *(recommended to create)* - place CSV/JSON datasets here
- `logs/` - application logs organized by date
- `test/` - unit and integration tests

## ⚙️ Setup & Installation

1. **Create a virtual environment**
   ```sh
   python -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   Create a `.env` file with keys like:
   ```env
   SMARTAPI_KEY=your_api_key
   SMARTAPI_SECRET=your_api_secret
   ```

## 🛠 Running the Backtester

```python
from src.utils.backtester import Backtester
from src.trading.example_strategy import my_strategy

# load historical data (pandas DataFrame)
# df = pd.read_csv('data/nifty_historical.csv', index_col='timestamp', parse_dates=True)

bt = Backtester(initial_capital=100000)
report = bt.run_backtest(df, my_strategy)
print(report)
```

## 🧪 Testing

Tests are located under `test/`. Run them with:

```sh
pytest --cov=src
```

## 📄 Product Requirements (PRD)

This project is intended to support algorithmic options trading research for the NIFTY index. It should be modular, configurable, and able to:

1. **Fetch live market data** using SmartAPI.
2. **Simulate strategies** on historical or synthetic data.
3. **Generate signals** using simple ML/AI models.
4. **Record paper trades** and analyze performance metrics.
5. **Deployable as a service** with clear configuration and logging.

### 🔍 Advanced Requirements

#### **Core Features**
- **Live Data Ingestion**
  - Connect to SmartAPI and other exchanges via configurable adapters.
  - Support websocket & REST with automatic reconnects and back‑off strategies.
  - Normalise data into a common schema with timestamp, open/high/low/close/volume.

- **Historical Data Engine**
  - Import CSV/Parquet files, database sources, or generate synthetic data.
  - Provide resampling, merging, and caching layers for performance.
  - Ensure reproducibility with seedable random generators.

- **Strategy Interface**
  - Define a pluggable strategy API: `def on_bar(bar, state):` or `strategy(df, params)`.
  - Allow parameter optimisation and walk‑forward testing.
  - Support long/short, options, and multi‑symbol portfolios.

- **Backtesting & Analysis**
  - Run simulations with transaction costs, slippage models, and margin checks.
  - Produce detailed reports: equity curve, drawdown, Sharpe, max DD, trade list.
  - Export results as JSON/CSV and visualize via optional dashboard.

- **AI/ML Signal Factory**
  - Wrap ML models (scikit‑learn, TensorFlow, PyTorch) behind a simple API.
  - Provide feature pipelines for technical indicators, sentiment, news.
  - Allow training, evaluation, and deployment of models within the same framework.

- **Paper Trading & Execution**
  - Maintain stateful order book simulation for paper trades.
  - Plug into brokers (via SmartAPI or REST mocks) for live order placement.
  - Log all actions with timestamps, P&L, fees, and order statuses.

- **Configuration & Security**
  - Centralised config using `.env`, `yaml`, or `toml`; override via CLI flags.
  - Sensitive credentials stored securely (env vars or secrets manager).
  - Role‑based access control for any web/dashboard components.

- **Monitoring & Ops**
  - Structured logging (JSON) at `INFO`/`DEBUG`/`ERROR` levels.
  - Health endpoints or internal heartbeat metrics for uptime monitoring.
  - Error reporting integrated with Sentry or equivalent.

#### **User Stories**
- As a quant researcher, I want to run a backtest with custom parameters and compare multiple strategies side‑by‑side.
- As a developer, I need a reproducible way to generate synthetic market data for stress testing.
- As an analyst, I want to view performance metrics on a simple web dashboard with charts.
- As an ops engineer, I must be able to deploy the service in Docker with environment‑specific configs.

#### **Non-Functional Requirements**
- **Performance:** Handle datasets of 10+ years of tick-level data efficiently.
- **Reliability:** Tolerate intermittent network failures without data loss.
- **Scalability:** Allow horizontal scaling of backtest workers via message queue.
- **Maintainability:** Code must be well‑documented and covered by automated tests (>90%).
- **Security:** Ensure no exposure of API keys in logs or error reports.

#### **Acceptance Criteria**
- End‑to‑end backtest can be executed via CLI with a config file and generates a result file.
- Live market data adapter recovers from disconnects within 30 seconds.
- ML model training pipeline logs hyperparameters and metrics.
- Docker image builds reproducibly and runs all unit tests in CI.

#### **Metrics & KPIs**
- Number of successful backtests executed per day.
- Average latency for live tick processing.
- Test coverage percentage and build-pass rate in CI.
- Mean time to recover (MTTR) from outages.
- Accuracy/F1 score of deployed ML signals (if applicable).

## 🚀 Production Considerations


## 📈 Future Improvements



*This README serves as a starting point for developers and can be extended as the project matures.*
See the full, advanced Product Requirements Document: [docs/PRD.md](docs/PRD.md)