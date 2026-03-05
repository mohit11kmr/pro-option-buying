# 🚀 Nifty Options Trading System - Enterprise Edition

**Advanced algorithmic trading platform with AI/ML signals, multi-broker support, real-time execution, and production deployment capabilities.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](Dockerfile.prod)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue)](k8s/)

## 📊 Overview

This enterprise-grade trading system provides:

- **🤖 AI/ML-Powered Signals**: LSTM/Transformer models, regime detection, RL optimization
- **📈 Live Trading Execution**: Real-time order management with SmartAPI integration
- **📱 Multi-Platform Notifications**: Telegram & Discord bots with rich interfaces
- **🔍 Risk Management**: Monte Carlo simulations, stress testing, VaR/CVaR analysis
- **🌐 Ecosystem Integration**: TradingView webhooks, 3Commas smart trades, multi-broker support
- **☁️ Production Ready**: Docker, Kubernetes, CI/CD with auto-scaling
- **📊 Professional API**: REST API v2 with OpenAPI/Swagger documentation

## 🧭 **Quick Navigation**

| **I want to...** | **Go to...** |
|------------------|--------------|
| **🚀 Start the application** | [`scripts/run_dashboard.sh`](scripts/run_dashboard.sh) |
| **⚙️ Configure the system** | [`config/.env`](config/.env) |
| **📚 Read documentation** | [`docs/`](docs/) directory |
| **💻 View source code** | [`src/`](src/) directory |
| **🧪 Run tests** | [`test/`](test/) directory |
| **🌐 Access web interface** | [`frontend/`](frontend/) directory |
| **☁️ Deploy to production** | [`k8s/deployment.yaml`](k8s/deployment.yaml) |
| **🔄 Check CI/CD status** | [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) |

## 📂 **Project Structure**

**📖 [Complete Structure Guide](.project_structure.md)** - Detailed file organization reference

## 🎯 Key Features

### Phase 9: Live Execution & Order Management
- ✅ Real-time order placement, modification, cancellation
- ✅ Live P&L tracking with WebSocket streaming (500ms updates)
- ✅ Position management with automatic hedging
- ✅ SmartAPI integration with paper trading fallback
- ✅ Comprehensive trade logging and audit trails

### Phase 10: Advanced ML & Signal Ensemble
- ✅ **Regime Classifier**: Bull/Bear/Sideways market detection using Random Forest + Gradient Boosting
- ✅ **Deep Price Predictor**: LSTM (128→64→32) + Transformer ensemble for 5-day forecasts
- ✅ **RL Optimizer**: Q-Learning parameter optimization for MA periods, SL/TP levels
- ✅ Signal confidence scoring and ensemble voting

### Phase 11: Bot Integration & Notifications
- ✅ **Telegram Bot**: 8 commands (/status, /signal, /trades, /pnl, /position, /close, /alerts, /help)
- ✅ **Discord Bot**: Rich embeds with portfolio status, P&L reports, signal notifications
- ✅ Real-time trade execution via bot commands
- ✅ Customizable alert routing and notification preferences

### Phase 12: Risk Analysis & Stress Testing
- ✅ **Monte Carlo Simulator**: 10,000 path simulations with GBM modeling
- ✅ **VaR/CVaR Analysis**: Value at Risk and Conditional VaR at 95% confidence
- ✅ **Stress Tester**: 5 realistic scenarios (Market Crash, Volatility Spike, Sustained Decline, Gap Down, Liquidity Crunch)
- ✅ Portfolio sensitivity analysis and recovery time estimation

### Phase 13: Production Deployment
- ✅ **Docker**: Multi-stage production build (500MB optimized image)
- ✅ **Kubernetes**: Auto-scaling deployment (2-10 pods) with PostgreSQL + Redis
- ✅ **CI/CD**: GitHub Actions with 6 stages (test → quality → build → security → deploy-dev → deploy-prod)
- ✅ **Health Checks**: Liveness/readiness probes, rolling updates, zero downtime

### Phase 14: Ecosystem Integration
- ✅ **REST API v2**: Professional API with JWT authentication and OpenAPI/Swagger docs
- ✅ **TradingView Integration**: Webhook receiver with HMAC verification for automated signals
- ✅ **3Commas Integration**: Smart trade creation and synchronization
- ✅ **Multi-Broker Adapter**: Unified interface for Angel One, Zerodha, Shoonya brokers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SIGNALS                         │
│  (TradingView, 3Commas, AI Models, Discord/Telegram)        │
└─────────────────┬───────────────────────────────────────────┘
                  │ webhooks + REST API
┌─────────────────▼───────────────────────────────────────────┐
│              API v2 (REST + WebSocket)                       │
│  Authentication │ JWT │ Rate Limiting │ Documentation       │
└─────────────────┬───────────────────────────────────────────┘
                  │
  ┌───────────────┼───────────────┐
  │               │               │
  ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│   ML     │  │  Order   │  │ Position │
│ Models   │  │ Manager  │  │ Manager  │
└──────────┘  └─────┬────┘  └──────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    ┌──────────┬──────────┬──────────┐
    │  Angel   │ Zerodha  │ Shoonya  │
    │   One    │   Kite   │  Neo     │
    └──────────┴──────────┴──────────┘
        │           │           │
        └───────────┼───────────┘
            Market Execution
```

## 📦 Project Structure

```
├── src/
│   ├── utils/
│   │   ├── live_order_executor.py      # Live trading execution
│   │   ├── ml/
│   │   │   ├── regime_classifier.py    # Market regime detection
│   │   │   ├── deep_price_predictor.py # LSTM/Transformer forecasting
│   │   │   └── rl_optimizer.py         # Parameter optimization
│   │   ├── telegram_bot.py             # Telegram notifications
│   │   ├── discord_bot.py              # Discord notifications
│   │   ├── monte_carlo_simulator.py    # Risk simulations
│   │   └── stress_tester.py            # Stress testing
│   ├── web/
│   │   ├── app.py                      # Main Flask application
│   │   ├── api_v2.py                   # REST API v2
│   │   ├── tradingview_integration.py  # TradingView webhooks
│   │   ├── threecommas_integration.py  # 3Commas API
│   │   └── multi_broker_adapter.py     # Multi-broker support
│   └── cli/
│       └── main.py                     # CLI interface
├── frontend/
│   ├── live-trading.html               # Real-time trading dashboard
│   └── [other HTML files]
├── k8s/
│   └── deployment.yaml                 # Kubernetes manifests
├── .github/workflows/
│   └── deploy.yml                      # CI/CD pipeline
├── test/
│   ├── test_new_modules.py             # Comprehensive test suite
│   └── [other test files]
├── Dockerfile.prod                     # Production Docker build
├── setup_postgres.py                   # Database migration script
└── requirements.txt                    # Python dependencies
```

## ⚙️ Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd nifty_options

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your credentials:

```env
# Angel One API Credentials
API_KEY=your_api_key_here
SECRET_KEY=your_api_secret_here
USER_ID=your_client_code
MPIN=your_mpin
TOTP_SECRET=your_totp_secret

# Bot Tokens
TELEGRAM_BOT_TOKEN=your_telegram_token
DISCORD_BOT_TOKEN=your_discord_token

# Database (Production)
DATABASE_URL=postgresql://trading:trading@localhost:5432/trading
REDIS_URL=redis://localhost:6379/0

# External Integrations
TRADINGVIEW_WEBHOOK_SECRET=your_webhook_secret
THREECOMMAS_API_KEY=your_3commas_key
THREECOMMAS_API_SECRET=your_3commas_secret

# Flask Settings
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

### 3. Database Setup

For PostgreSQL (Production):
```bash
python setup_postgres.py
```

For SQLite (Development):
```bash
# Database is auto-created on first run
```

### 4. Run the Application

```bash
# Start the web application
python -m src.web.app

# Or use the dashboard script
./run_dashboard.sh
```

Access the application at `http://localhost:5000`

## 🚀 Usage Examples

### Live Order Execution

```python
from src.utils.live_order_executor import LiveOrderExecutor

executor = LiveOrderExecutor(
    api_key="your_key",
    client_code="your_client",
    password="your_pin",
    totp_secret="your_totp"
)

# Place a live order
order = executor.place_live_order(
    symbol="NIFTY",
    quantity=1,
    entry_price=24800,
    stop_loss=24650,
    target=25100
)
print(f"Order placed: {order['order_id']}")
```

### ML Regime Detection

```python
from src.utils.ml.regime_classifier import RegimeClassifier

classifier = RegimeClassifier()
classifier.fit(historical_data)

regime = classifier.predict(current_data)
print(f"Current regime: {regime['regime']} ({regime['confidence']:.1%})")
```

### Monte Carlo Risk Analysis

```python
from src.utils.monte_carlo_simulator import MonteCarloSimulator

simulator = MonteCarloSimulator()
var_result = simulator.calculate_var_cvar(returns)

print(f"95% VaR: {var_result['VaR_95']:.2%}")
print(f"95% CVaR: {var_result['CVaR_95']:.2%}")
```

### Telegram Bot Commands

Start a conversation with your bot and use:
- `/status` - Portfolio overview
- `/signal` - Latest AI signals
- `/trades` - Active trades
- `/pnl` - Daily P&L report
- `/position NIFTY` - Position details
- `/close <order_id>` - Close a trade

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test/ -v

# Run specific test file
pytest test/test_new_modules.py -v

# Run with coverage
pytest test/ --cov=src --cov-report=html
```

## 🐳 Docker Deployment

### Build Production Image

```bash
# Build multi-stage production image
docker build -f Dockerfile.prod -t nifty-trading:latest .

# Run locally
docker run -p 5000:5000 --env-file .env nifty-trading:latest
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -n trading
kubectl get services -n trading

# View logs
kubectl logs -n trading deployment/api-deployment
```

## 🔧 API Documentation

The REST API v2 includes comprehensive OpenAPI/Swagger documentation:

- **Base URL**: `http://localhost:5000/api/v2`
- **Documentation**: `http://localhost:5000/api/v2/docs`
- **Authentication**: JWT tokens required for most endpoints

### Key Endpoints

```bash
# Authentication
POST /api/v2/auth/login

# Trades
GET  /api/v2/trades/active
GET  /api/v2/trades/{order_id}
DELETE /api/v2/trades/{order_id}

# Portfolio
GET /api/v2/portfolio/summary
GET /api/v2/portfolio/allocation

# Signals
GET /api/v2/signals/latest

# Brokers
GET /api/v2/brokers/list
POST /api/v2/brokers/{id}/sync

# Backtesting
POST /api/v2/backtest/run
```

## 🤖 Bot Integration

### Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Add your token to `.env`
3. Start the bot: `python -m src.utils.telegram_bot`

### Discord Bot Setup

1. Create application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Add bot token to `.env`
3. Invite bot to your server
4. Start the bot: `python -m src.utils.discord_bot`

## 🔗 External Integrations

### TradingView Webhooks

1. Set up webhook URL: `https://your-domain.com/hooks/tradingview`
2. Configure secret in TradingView and `.env`
3. Use the provided Pine Script for alerts

### 3Commas Smart Trades

1. Get API credentials from 3Commas
2. Add to `.env` file
3. Signals automatically create smart trades

## 📊 Monitoring & Health Checks

- **Health Check**: `GET /health` - Liveness probe
- **Readiness Check**: `GET /ready` - Readiness probe
- **Metrics**: Prometheus-compatible metrics available
- **Logs**: Structured JSON logging with rotation

## 🔒 Security Features

- JWT token authentication
- HMAC signature verification for webhooks
- Rate limiting on API endpoints
- Network policies in Kubernetes
- Non-root container execution
- Secrets management via Kubernetes

## 📈 Performance

- **Auto-scaling**: 2-10 pods based on CPU/memory
- **Caching**: Redis for session and signal caching
- **Database**: PostgreSQL with connection pooling
- **ML Inference**: Optimized TensorFlow models
- **WebSocket**: Real-time streaming with 500ms updates

## 🛠️ Development

### Code Quality

```bash
# Linting
flake8 src/

# Type checking
mypy src/

# Formatting
black src/
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes with tests
3. Update documentation
4. Create pull request

## 📚 Documentation

- [Implementation Complete](./IMPLEMENTATION_COMPLETE.md) - Detailed feature documentation
- [API Documentation](./api_docs.md) - REST API reference
- [Deployment Guide](./deployment.md) - Production setup instructions
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes. Use at your own risk. Always test thoroughly before deploying with real money.

---

**Built with ❤️ for the Indian trading community**

*Last updated: March 2026*

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