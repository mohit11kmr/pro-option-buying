# Self-Learning Trading System

## Planning
- [x] Study all existing ML modules
- [x] Write implementation plan
- [x] Get user approval

## Execution
- [x] Extend `db_manager.py` — New tables for learning data
- [x] Create `self_learning_engine.py` — Core auto-training brain
  - [x] Live data collection pipeline
  - [x] Signal accuracy tracker (prediction vs outcome)
  - [x] Adaptive weight optimizer
  - [x] Auto-retrain scheduler
  - [x] Performance reporter
- [x] Integrate into `app.py` — Background training thread + API endpoints
- [x] Integrate into `signal_generator.py` — Feedback loop
- [x] Add training status to frontend dashboard

- [x] Start server and verify auto-learning cycle
- [x] Write walkthrough

## Phase 3: Visibility & Trust (Visual AI Reasoning)
- [x] Update `ai-signal.html` with "Live AI Reasoning Stream"
- [x] Implement "AI Confidence Gauge" widget
- [x] Add "Logic Heartbeat" animation (synchronized with market updates)
- [x] Create "Detailed Signal Breakdown" (Actionable Entry/SL/Target)
- [x] User testing to verify "Belief/Trust" objective

## Phase 4: Price Change Analytics
- [x] Implement `get_day_open` in `market_data.py`
- [x] Update `app.py` price stream with open price
- [x] Add "+/- Change from Open" display to `ai-signal.html`

## Phase 6: Advanced Excellence (via OpenCode)
- [x] Implement "GIFT Nifty Tracker" in header using `opencode`
- [x] Implement "Global Market Correlation" indicators using `opencode`
- [x] Verify OpenCode changes and ensure dashboard stability
- [x] Capture proof of enhanced global insights

## Phase 6b: Multi-Expert AI Voting System
- [x] Implement 3 AI Expert panels (Trend, Flow, Sentiment) using `opencode`
- [x] Add "Triple Lock" consensus indicator
- [x] Verify expert voting UI on dashboard

## Phase 7A: Live Options Chain Dashboard (Institutional)
- [x] Create backend API endpoints for options chain data, PCR, Max Pain
- [x] Build `options-chain.html` frontend page with live chain table
- [x] Add PCR Gauge + Max Pain indicator
- [x] Add OI Change heatmap with color coding
- [x] Add live Greeks columns (Δ Γ Θ V) via `greeks_analyzer.py`
- [x] Add strike recommendation badges via `strike_selector.py`
- [x] Add route to navigation header on all pages
- [x] Verify full options chain page rendering

## Phase 7B: Risk Management Console
- [x] Add risk management section to `ai-signal.html`
- [x] Position Sizer (capital → lot size based on SL)
- [x] Max Daily Loss limit with auto-disable
- [x] Risk:Reward Ratio display on every signal
- [x] Drawdown tracker with equity curve
- [x] Capital utilization meter

## Phase 7C: Multi-Timeframe Analysis
- [x] MTF Grid showing 5m/15m/1h/Daily signals
- [x] Alignment Score indicator

## Phase 7D: Trade Journal & PnL Analytics
- [x] Create `paper_trades` table in `db_manager.py` with entry/exit/PnL tracking.
- [x] Implement API endpoints (`/api/trades/execute`, `/api/trades/close`, `/api/trades/summary`).
- [x] Build institutional `trade-journal.html` with real-time stats (Win Rate, Profit Factor).
- [x] Add "One-Click Paper Execute" button to `ai-signal.html` risk console.
- [x] Integrate equity curve and trade distribution charts.
- [x] Update site-wide navigation with "Journal" link.

## Phase 8: Deployment & Sharing
- [x] **GitHub Integration**
    - [x] Create `.gitignore` and `.env.example`.
    - [x] Initialize Git repository.
    - [x] Add remote origin `https://github.com/mohit11kmr/pro-option-buying.git`.
    - [x] Push code to GitHub.
