# Technical Design Document (TDD)
## Nifty Options Trading System v3.1

**Version:** 3.1  
**Date:** 27 February 2026  
**Architecture:** Microservices-Ready Monolith  
**Tech Stack:** Python Flask, HTML5/CSS3/JS, SQLite  

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                               │
│  Dashboard │ Signals │ Orders │ Performance │ Risk │ Analysis   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                            │
│  Flask Web Server (Port 5055) + Socket.IO Real-Time             │
│  - HTML5 Templates                                              │
│  - CSS3 Styling (Dark Mode)                                     │
│  - JavaScript Controllers (Chart.js, WebSockets)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ AI Engines   │  │ Paper Trader │  │ Risk Manager │          │
│  │ - Signal Gen │  │ - Execute    │  │ - Monitor    │          │
│  │ - ML Models  │  │ - Track      │  │ - Calc Risk  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ MCX Engine   │  │ Broker API   │  │ Analytics   │          │
│  │ - Options    │  │ - SmartAPI   │  │ - P&L Calc  │          │
│  │ - Commodities│  │ - Orders     │  │ - Stats     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DATA ACCESS LAYER                             │
│  Database (SQLite) │ File Storage (CSV/JSON)                    │
│  - Trades         │ - Paper Trades (CSV)                        │
│  - Performance    │ - MCX Trades (JSON)                         │
│  - Settings       │ - Risk State (JSON)                         │
│  - Audit Logs     │ - Active Trades (JSON)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                         │
│  Angel One SmartAPI │ Market Data │ Telegram │ Yahoo Finance    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Hierarchy

```
src/
├── web/
│   ├── control_center.py          # Flask app & main routes
│   └── auth.py                    # JWT authentication
├── trading/
│   ├── paper_trader.py             # Virtual trade execution
│   ├── ai_market_sentry.py         # Signal generation (RF, LSTM, SVM)
│   ├── technical_indicators.py     # RSI, MACD, Bollinger Bands
│   └── mcx_engine.py               # Commodity trading
├── utils/
│   ├── database.py                 # SQLite operations
│   ├── broker_api.py               # Angel One SmartAPI wrapper
│   ├── risk_manager.py             # Risk calculation
│   ├── analytics_engine.py         # P&L & performance stats
│   └── telegram_notifier.py        # Telegram alerts
└── models/
    ├── trade.py                    # Trade model
    ├── signal.py                   # Signal model
    └── audit_log.py                # Audit trail
```

---

## 2. Data Flow Architecture

### 2.1 Market Data Pipeline

```
Broker API (Angel One)
    ↓
[get_spot_price()] → Spot Price (e.g., 23,500)
    ↓
[get_option_chain()] → Option Chain (50+ strikes)
    ↓
[get_vix()] → VIX Index (16.5)
    ↓
Technical Indicators Engine
    ├─ RSI(14)          → 58.2
    ├─ MACD(12,26,9)    → -0.45
    ├─ Bollinger Bands   → Upper: 23,650 | Lower: 23,350
    └─ Moving Averages   → 50MA: 23,480 | 200MA: 23,200
    ↓
WebSocket Event: market_update
    ↓
Client Dashboard (Real-time Chart, Metrics)
```

### 2.2 Signal Generation Pipeline

```
System State (Spot, VIX, PCR, Chain)
    ↓
AI Market Sentry
    ├─ Random Forest Model (92% weight)
    ├─ LSTM Neural Network (85% weight)
    └─ SVM Classifier (79% weight)
    ↓
Signal Aggregation (Confidence = avg of models)
    ↓
Pattern Detection
    ├─ Diamond Breakouts
    ├─ Head & Shoulders
    └─ Flag Formations
    ↓
Sentiment Analysis
    ├─ Market Sentiment Score
    └─ Indicator Agreement
    ↓
Signal Output: {
    "strike": 23500,
    "direction": "BUY_CALL",
    "confidence": 87.3,
    "entry": 45.50,
    "sl": 42.00,
    "target": 52.00,
    "reason": "Diamond Breakout + Bullish RSI"
}
    ↓
WebSocket Event: new_ai_setup
    ↓
Client Notification + Optional Auto-Execute
```

### 2.3 Trade Execution Pipeline

```
Signal Generated
    ↓
[Check Risk Limits]
    ├─ Daily Loss < -₹20,000? → REJECT
    ├─ Position Risk > 2%? → REDUCE/REJECT
    └─ Leverage > 5x? → REJECT
    ↓
[Calculate Position Size]
    ├─ Risk Amount = Account * 1%
    ├─ Quantity = Risk Amount / (Entry - SL)
    └─ Lot Size = Round to valid lot
    ↓
Paper Trader OR Broker API
    ├─ Paper: Create virtual trade record
    └─ Live: POST /order/v1/placeOrder
    ↓
Trade Execution
    ├─ Status: OPEN
    ├─ Entry Price: {entry}
    ├─ Entry Time: {timestamp}
    └─ Save to nifty_paper_trades.csv
    ↓
WebSocket Event: portfolio_update
    ↓
Dashboard Updates with Real-Time P&L
```

### 2.4 Trade Monitoring Pipeline

```
[Every 1 second during market hours]
    ↓
Spot Price Update
    ├─ Option Current Price
    ├─ Calculate P&L = (Current - Entry) * Qty
    └─ Check Exit Conditions
    ↓
Exit Conditions Check
    ├─ Hit Target? → CLOSE (Status: CLOSED)
    ├─ Hit SL? → CLOSE (Status: CLOSED)
    ├─ Max Duration Reached? → CLOSE (Status: EXPIRED)
    └─ Manual Close? → CLOSE (Status: CLOSED)
    ↓
Update Trade Record
    ├─ Exit Price
    ├─ Exit Time
    ├─ Final P&L
    └─ Save to CSV/DB
    ↓
WebSocket Event: portfolio_update with updated P&L
    ↓
Charts & Metrics Refresh (Dashboard)
```

---

## 3. Database Schema

### 3.1 SQLite Tables

#### trades
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity INTEGER,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    pnl REAL,
    status TEXT,  -- OPEN, CLOSED, CANCELLED
    strategy TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### signals
```sql
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_type TEXT,  -- BUY, SELL, EXIT
    confidence REAL,
    entry_price REAL,
    target_price REAL,
    stop_loss REAL,
    generated_at TIMESTAMP,
    model_breakdown TEXT,  -- JSON
    pattern TEXT,
    sentiment_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    user_id TEXT,
    action TEXT,
    status TEXT,
    details TEXT,  -- JSON
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 File-Based Storage

#### nifty_paper_trades.csv
```
Timestamp,Action,Symbol,Strike,Entry,Exit,Qty,PnL,Status,Reason
2026-02-27 10:30:15,BUY_DIRECTIONAL,NIFTY,23500,45.50,48.20,100,270,CLOSED,Diamond Breakout
2026-02-27 11:15:42,BUY_CALL,NIFTY,23450,35.80,,50,0,OPEN,RSI Signal
```

#### mcx_paper_trades.json
```json
{
    "active": [
        {
            "timestamp": "2026-02-27 10:30:15",
            "commodity": "CRUDEOIL",
            "direction": "BUY_CALL",
            "strike": 6500,
            "entry": 125.50,
            "current": 128.30,
            "pnl": 280,
            "status": "OPEN"
        }
    ],
    "history": [...]
}
```

#### risk_state.json
```json
{
    "daily_loss": -8500,
    "daily_limit": -20000,
    "total_exposure": 245000,
    "leverage": 2.3,
    "position_risk_pct": 2.1,
    "max_leverage": 5.0,
    "correlation_matrix": {...},
    "last_update": "2026-02-27T15:45:30Z"
}
```

---

## 4. API Specifications

### 4.1 REST API Endpoints

#### Market Data
```
GET /api/market/{symbol}
Response: {
    "spot": 23500.5,
    "vix": 16.8,
    "pcr": 1.25,
    "chain": [...],
    "technical_indicators": {...}
}

GET /api/historical/{symbol}
Response: [{time, open, high, low, close, volume}, ...]

GET /api/volatility/{symbol}
Response: {
    "iv": 18.5,
    "realized": 16.2,
    "term_structure": [...]
}
```

#### Signal APIs
```
GET /api/signals
Query: ?symbol=NIFTY&type=BUY&confidence=80&limit=10
Response: [{id, symbol, type, confidence, entry, target, sl, ...}, ...]

POST /api/signals/{id}/execute
Body: {action: "BUY", override_risk: false}
Response: {status: "success", trade_id: 123}

GET /api/signals/{id}/backtest
Response: {
    win_rate: 68.5,
    avg_return: 2.34,
    max_loss: -1500,
    total_trades: 150
}
```

#### Trading APIs
```
POST /api/trades/execute
Body: {
    symbol: "NIFTY",
    type: "BUY_CALL",
    entry: 45.50,
    sl: 42.00,
    target: 52.00,
    quantity: 100
}
Response: {trade_id: 456, status: "OPEN", pnl: 0}

GET /api/trades/active
Response: [{id, symbol, entry, current, pnl, sl, target, ...}, ...]

POST /api/trades/{id}/close
Body: {exit_price: 48.50}
Response: {trade_id: 456, status: "CLOSED", pnl: 300}

GET /api/trades/history?date=2026-02-27
Response: [{id, symbol, entry, exit, pnl, ...}, ...]
```

#### Performance APIs
```
GET /api/performance/summary
Response: {
    daily_pnl: 2340,
    total_pnl: 45600,
    win_rate: 68.5,
    avg_return: 2.34,
    sharpe_ratio: 1.8,
    max_drawdown: 12.5
}

GET /api/performance/journal?date=2026-02-27
Response: [{timestamp, type, entry, exit, pnl, ...}, ...]

POST /api/performance/export
Body: {format: "csv", period: "monthly"}
Response: File download
```

#### Risk APIs
```
GET /api/risk/status
Response: {
    daily_loss: -8500,
    limit: -20000,
    exposure: 245000,
    leverage: 2.3,
    position_risk: 2.1,
    var_95: 12450,
    correlation_matrix: {...}
}

POST /api/risk/limits
Body: {daily_loss_limit: -20000, max_leverage: 5.0, ...}
Response: {status: "updated"}

GET /api/risk/warnings
Response: [{type: "DAILY_LOSS_WARNING", severity: "HIGH", ...}, ...]
```

### 4.2 WebSocket Events (Socket.IO)

#### Client → Server

```javascript
// Market selection
emit('change_index', {index: 'BANKNIFTY'})

// System toggle
emit('toggle_system', {
    component: 'nifty_sentry',  // or crude_sentry, ng_sentry, trader
    state: true
})

// Manual trade
emit('mcx_manual_trade', {
    commodity: 'CRUDEOIL',
    direction: 'BUY',
    price: 6500
})

// Trade closing
emit('mcx_close_trade', {commodity: 'CRUDEOIL'})

// Test signal
emit('test_ai_signal', {
    opt_type: 'CALL',
    strike: 23500,
    entry: 45.50,
    sl: 42.00,
    target: 52.00,
    reason: 'Test Signal'
})
```

#### Server → Client

```javascript
// Market data updates (every 10s)
socket.on('market_update', (data) => {
    // {selected_index, spot, vix, pcr, chain, technical_indicators}
})

// New AI signal
socket.on('new_ai_setup', (data) => {
    // {strike, opt_type, entry, sl, target, reason, confidence}
})

// Portfolio status
socket.on('portfolio_update', (data) => {
    // {active: [...], summary: [...]}
})

// Performance metrics
socket.on('performance_update', (data) => {
    // {total_pnl, win_rate, avg_return, ...}
})

// Commodity updates
socket.on('commodity_update', (data) => {
    // {oil, gas, ...}
})

// System status
socket.on('status_update', (data) => {
    // {nifty_sentry, crude_sentry, ng_sentry, trader_active, ...}
})
```

---

## 5. Technology Stack

### 5.1 Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | Flask | 2.3+ |
| Real-time | Flask-SocketIO | 5.3+ |
| Authentication | JWT | python-jose |
| Database | SQLite | 3.40+ |
| Broker API | SmartAPI | 1.3+ |
| ML Models | Scikit-learn, TensorFlow | 1.2, 2.12+ |
| Data Analysis | Pandas | 2.0+ |

### 5.2 Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| HTML | HTML5 | ES2020 |
| CSS | CSS3 + Bootstrap | 5.3+ |
| JavaScript | ES6+ | Socket.IO 4.7+ |
| Charts | Chart.js | 3.9+ |
| Icons | Bootstrap Icons | 1.11+ |
| Fonts | Google Fonts | Inter, JetBrains Mono |

### 5.3 DevOps
| Component | Technology |
|-----------|-----------|
| OS | Ubuntu 22.04 LTS |
| Container | Docker |
| Process Manager | Systemd / Gunicorn |
| Monitoring | Custom logging |
| Backup | Automated (hourly snapshots) |

---

## 6. Implementation Details

### 6.1 AI Signal Generation Flow

```python
# 1. Data Collection
market_data = {
    'spot': get_spot_price('NIFTY'),
    'vix': get_vix(),
    'chain': get_option_chain(spot, vix),
    'indicators': get_technical_indicators()
}

# 2. Model Predictions
rf_signal = random_forest_model.predict(market_data)      # 92% confidence cap
lstm_signal = lstm_model.predict(market_data)              # 85% confidence cap
svm_signal = svm_model.predict(market_data)                # 79% confidence cap

# 3. Confidence Calculation
confidence = (rf_signal * 0.92 + lstm_signal * 0.85 + svm_signal * 0.79) / 3
# Result: 85.3% confidence

# 4. Pattern Detection
pattern = detect_patterns(chain_data, indicators)
# Result: "Diamond Breakout at 23500 CE"

# 5. Sentiment Analysis
sentiment = analyze_market_sentiment(chain, pcr, vix)
# Result: +0.72 (Bullish)

# 6. Final Signal
signal = {
    'strike': 23500,
    'opt_type': 'CALL',
    'entry': 45.50,
    'sl': 42.00,
    'target': 52.00,
    'confidence': 85.3,
    'pattern': 'Diamond Breakout',
    'sentiment': 0.72,
    'reason': 'Bullish RSI + Positive PCR'
}

return signal
```

### 6.2 Risk Management Algorithm

```python
def evaluate_trade_risk(signal, account_size, current_positions):
    # 1. Check Daily Loss
    if daily_loss < -account_size * 0.10:
        return {"allowed": False, "reason": "Daily loss limit exceeded"}
    
    # 2. Calculate Position Risk
    risk_per_trade = abs(signal['entry'] - signal['sl']) * signal['quantity']
    total_risk = sum([pos['risk'] for pos in current_positions]) + risk_per_trade
    risk_pct = total_risk / account_size
    
    if risk_pct > 0.02:
        return {"allowed": False, "reason": "Position risk exceeds 2%"}
    
    # 3. Check Leverage
    margin_required = signal['quantity'] * signal['entry'] * 0.10
    leverage = account_value / available_margin
    
    if leverage > 5.0:
        return {"allowed": False, "reason": "Leverage exceeds 5x"}
    
    # 4. Correlation Check
    correlation = calculate_correlation(signal['symbol'], current_positions)
    if correlation > 0.8:
        return {"allowed": False, "reason": "High correlation with existing position"}
    
    return {"allowed": True, "risk_pct": risk_pct, "leverage": leverage}
```

### 6.3 Performance Calculation

```python
def calculate_performance(trades, start_date, end_date):
    closed_trades = [t for t in trades if t['status'] == 'CLOSED']
    
    # Win Rate
    winners = [t for t in closed_trades if t['pnl'] > 0]
    win_rate = len(winners) / len(closed_trades) * 100
    
    # Average Return
    avg_return = sum([t['pnl'] for t in closed_trades]) / len(closed_trades)
    
    # Sharpe Ratio
    returns = [t['pnl'] / account_size for t in closed_trades]
    daily_std = np.std(returns)
    sharpe = (np.mean(returns) / daily_std) * np.sqrt(252)
    
    # Maximum Drawdown
    cumulative_pnl = []
    running_total = 0
    for t in closed_trades:
        running_total += t['pnl']
        cumulative_pnl.append(running_total)
    
    peak = cumulative_pnl[0]
    max_drawdown = 0
    for pnl in cumulative_pnl:
        peak = max(peak, pnl)
        drawdown = (peak - pnl) / peak
        max_drawdown = max(max_drawdown, drawdown)
    
    return {
        'win_rate': win_rate,
        'avg_return': avg_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown
    }
```

---

## 7. Security Architecture

### 7.1 Authentication Flow
```
1. User Login
   ├─ POST /login with credentials
   ├─ Verify against database
   └─ Return JWT token (24-hour expiry)

2. API Request
   ├─ Client includes token in header: Authorization: Bearer {token}
   ├─ Flask validates JWT signature
   └─ Proceed if valid, reject if expired/invalid

3. Token Refresh
   ├─ POST /refresh with expired token
   └─ Return new token if refresh token valid
```

### 7.2 Authorization Matrix
| Role | Dashboard | Signals | Execute | Risk | Admin |
|------|-----------|---------|---------|------|-------|
| Trader | ✅ | ✅ | ✅ | ✅ | ❌ |
| Analyst | ✅ | ✅ | ❌ | ✅ | ❌ |
| Admin | ✅ | ✅ | ✅ | ✅ | ✅ |

### 7.3 Data Protection
- **TLS 1.2+:** All data in transit encrypted
- **Password Hashing:** Bcrypt with salt (cost factor 12)
- **API Rate Limiting:** 100 requests/min per user
- **CSRF Protection:** Token validation on POST/PUT/DELETE
- **Audit Logging:** All trades, logins, config changes logged

---

## 8. Deployment & DevOps

### 8.1 Deployment Steps
```bash
# 1. Clone repository
git clone https://github.com/nifty-pro/system.git

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python3 migrate_db.py

# 5. Configure environment
cp .env.example .env
# Edit .env with API keys and credentials

# 6. Start application
python3 -m src.web.control_center

# 7. Access at http://localhost:5055
```

### 8.2 Production Deployment
```bash
# Using Gunicorn + Systemd
gunicorn -w 4 -b 0.0.0.0:5055 src.web.control_center:app

# Systemd service file: /etc/systemd/system/nifty-pro.service
[Service]
ExecStart=/home/user/nifty_options/venv/bin/gunicorn -w 4 src.web.control_center:app
WorkingDirectory=/home/user/nifty_options
Restart=always
```

### 8.3 Monitoring & Logging
- **Application Logs:** `/logs/2026-02-27/control_center.log`
- **Trade Logs:** `/logs/2026-02-27/trade.log`
- **System Logs:** Systemd journalctl
- **Metrics:** CPU, Memory, Disk usage (via psutil)
- **Alerts:** Email/Telegram on errors or risk breaches

---

## 9. Testing Strategy

### 9.1 Unit Tests
- Signal generation accuracy (target: 68%+ win rate)
- Risk calculation correctness
- P&L computation
- Date/time handling in different timezones

### 9.2 Integration Tests
- Broker API connectivity
- Trade execution end-to-end
- Database operations
- WebSocket real-time updates

### 9.3 System Tests
- Concurrent user load (target: 5-10 users)
- Data consistency across refreshes
- Error handling and recovery
- Backup and restore procedures

### 9.4 Performance Tests
- Page load times (target: < 3 seconds)
- Signal generation speed (target: < 2 seconds)
- WebSocket latency (target: < 500ms)

---

## 10. Known Limitations & Future Updates

### 10.1 Current Limitations
- Single-user session (multi-user planned for Phase 3)
- SQLite only (PostgreSQL upgrade planned)
- ML models trained on historical 2024-2026 data (model refresh every quarter)
- Broker connectivity restricted to Angel One (multi-broker in Phase 3)

### 10.2 Planned Enhancements
- Mobile app (React Native)
- Advanced ML (BERT for sentiment, GAN for signal generation)
- Multi-broker support (Zerodha, 5paisa)
- Cloud deployment (AWS/GCP)
- Advanced backtesting engine

