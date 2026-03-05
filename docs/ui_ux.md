# UI/UX Design Specification
## Nifty Options Trading System v3.1

**Version:** 3.1  
**Date:** 27 February 2026  
**Design System:** Modern, Professional, Dark-Mode First  
**Accessibility:** WCAG 2.1 AA Compliance  

---

## 1. Design System Foundation

### 1.1 Color Palette

#### Primary Colors
| Name | Hex | Usage | RGB |
|------|-----|-------|-----|
| **Primary Blue** | #2563EB | Links, CTAs, active states | 37, 99, 235 |
| **Secondary Green** | #10B981 | Success, profit, positive | 16, 185, 129 |
| **Accent Amber** | #F59E0B | Warnings, caution, pending | 245, 158, 11 |
| **Danger Red** | #EF4444 | Losses, errors, negative | 239, 68, 68 |

#### Background Colors
| Name | Hex | Usage |
|------|-----|-------|
| **Dark BG** | #0F172A | Main page background |
| **Card BG** | #1E293B | Card/panel backgrounds |
| **Border** | #334155 | Borders and separators |
| **Hover** | #475569 | Hover state backgrounds |

#### Text Colors
| Name | Hex | Usage |
|------|-----|-------|
| **Primary Text** | #F1F5F9 | Main content |
| **Secondary Text** | #94A3B8 | Labels, hints |
| **Muted Text** | #64748B | Disabled, inactive |
| **Accent Text** | #22C55E | Positive values |

#### Status Colors
| State | Color | Hex |
|-------|-------|-----|
| **Success** | Green | #22C55E |
| **Warning** | Amber | #FBBF24 |
| **Danger** | Red | #EF4444 |
| **Info** | Blue | #3B82F6 |

### 1.2 Typography

#### Font Stack
```css
Primary: 'Inter', 'Helvetica Neue', sans-serif
Mono: 'JetBrains Mono', 'Courier New', monospace
```

#### Font Weights
| Name | Weight | Usage |
|------|--------|-------|
| Regular | 400 | Body text |
| Medium | 500 | Emphasis, labels |
| Semibold | 600 | Subheadings |
| Bold | 700 | Headings |

#### Font Sizes
| Level | Size | Usage |
|-------|------|-------|
| H1 | 2.5rem (40px) | Page titles |
| H2 | 2rem (32px) | Section headers |
| H3 | 1.5rem (24px) | Subsection headers |
| H4 | 1.25rem (20px) | Card titles |
| H5 | 1rem (16px) | Labels |
| H6 | 0.875rem (14px) | Small labels |
| Body | 1rem (16px) | Main text |
| Small | 0.875rem (14px) | Helper text |
| Tiny | 0.75rem (12px) | Captions |

#### Line Heights
| Type | Value | Usage |
|------|-------|-------|
| Headings | 1.2 | Titles, headers |
| Body | 1.5 | Paragraph text |
| Code | 1.4 | Monospace text |

### 1.3 Spacing System (8px Grid)

```
8px   (0.5rem) - Tiny gaps
16px  (1rem)   - Small spacing
24px  (1.5rem) - Medium spacing
32px  (2rem)   - Large spacing
48px  (3rem)   - XL spacing
64px  (4rem)   - XXL spacing
```

### 1.4 Border & Radius

| Property | Value | Usage |
|----------|-------|-------|
| Border Width | 1px | Borders, outlines |
| Border Radius | 8px | Cards, buttons |
| Border Radius (Small) | 4px | Small components |
| Border Radius (Large) | 12px | Large panels |

### 1.5 Shadows

| Type | Value | Usage |
|------|-------|-------|
| Subtle | 0 1px 2px rgba(0,0,0,0.05) | Small elements |
| Base | 0 4px 6px rgba(0,0,0,0.1) | Cards, buttons |
| Medium | 0 10px 15px rgba(0,0,0,0.15) | Modals, dropdowns |
| Large | 0 20px 25px rgba(0,0,0,0.2) | Floating elements |

---

## 2. Layout & Grid

### 2.1 Responsive Breakpoints

| Device | Width | Columns | Sidebar |
|--------|-------|---------|---------|
| Mobile | 320px | 4 | Fullscreen |
| Tablet | 768px | 8 | Collapsible |
| Laptop | 1024px | 12 | Fixed 200px |
| Desktop | 1440px | 12 | Fixed 240px |

### 2.2 Main Layout

```
┌─────────────────────────────────────────┐
│  HEADER / NAVBAR (Fixed, Sticky)        │ h=56px
├─────────────────────────────────────────┤
│               MAIN CONTENT               │
│  ┌─────────────────────────────────────┐ │
│  │ LEFT   │                  │  RIGHT   │ │
│  │ 25%    │     65%          │  10%     │ │ (Desktop)
│  │        │                  │          │ │
│  │        │                  │          │ │
│  │ Mobile: Stack Full Width │          │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  Footer (Desktop only)                   │
└─────────────────────────────────────────┘
```

### 2.3 Content Spacing

```
Page Container: 1200px max-width
Content Padding: 16px (mobile), 24px (tablet), 32px (desktop)
Column Gap: 24px
Row Gap: 24px
Card Padding: 16px (small), 20px (medium), 24px (large)
```

---

## 3. Component Library

### 3.1 Navbar Component

**Height:** 56px (fixed)  
**Sticky:** Yes, on scroll  
**Background:** Dark (#1E293B)  
**Border:** Bottom 1px solid #334155  

**Sections:**
```
[Logo] [ Nav Links ] [ Right: Theme/Bell/Profile ]

Left (200px):
- Logo icon (32x32)
- App name "NiftyPro"
- Responsive: Logo only on mobile

Center (auto):
- Dashboard (active indicator)
- Signals
- Orders
- Performance
- Risk
- Analysis
- Settings
- Mobile: Hamburger menu

Right (150px):
- Theme Toggle (Moon icon)
- Notifications (Bell icon + badge)
- Profile Dropdown

Mobile (< 768px):
- Hamburger menu (replaces nav links)
- Logo visible always
```

**Interactions:**
- Hover: Background 15% lighter
- Active: Underline + color change
- Mobile: Slide-out menu from left
- Sticky: Remains visible on scroll

### 3.2 Metric Card Component

**Size:** 24% width (4-column grid)  
**Background:** #1E293B  
**Border:** 1px solid #334155  
**Padding:** 20px  
**Border-radius:** 8px  

**Structure:**
```
┌──────────────────────┐
│ Label (small) ⓘ      │ (14px, secondary color)
│ ₹2,340.50            │ (32px, bold, status color)
│ +12.3% portfolio     │ (12px, secondary)
└──────────────────────┘
```

**States:**
- Normal: #1E293B border
- Hover: Border color → primary blue, shadow up
- Positive: Value color → green
- Negative: Value color → red
- Neutral: Value color → blue

### 3.3 Signal Card Component

**Size:** 100% width in list, responsive grid in gallery  
**Background:** #1E293B  
**Border:** 1px solid #334155  
**Padding:** 16px  
**Border-radius:** 8px  
**Gap:** 12px  

**Structure:**
```
┌─────────────────────────────────────────┐
│ NIFTY-CALL        │ 10:30:45    │ 87%  │ (Header)
├─────────────────────────────────────────┤
│ [BUY] Confidence  │ RF:92% LSTM:85% ... │ (Meta)
├─────────────────────────────────────────┤
│ Entry: ₹45.50     │ SL: ₹42.00         │ (2-col)
│ Target: ₹52.00    │ R/R: 2.5x          │
├─────────────────────────────────────────┤
│ [Execute] [Eval] [Save] [Share]        │ (Actions)
└─────────────────────────────────────────┘
```

**Actions:**
- **Execute:** Primary blue button + hover effect
- **Eval:** Outline button, opens modal
- **Save:** Favorite icon (toggles)
- **Share:** Share icon + copy URL

### 3.4 Chart Component

**Type:** Lightweight Charts / Chart.js  
**Height:** 300px (responsive)  
**Background:** #1E293B  
**Border:** 1px solid #334155  
**Padding:** 16px  

**Features:**
- Candlestick chart (primary)
- Volume bars (secondary y-axis)
- 5+ technical indicators (overlays)
- Legend (toggle-able)
- Cross-hair cursor
- Interval selectors (1m, 5m, 15m, hourly, daily)
- Zoom/Pan enabled

**Colors:**
- Bullish candle: #10B981 (green)
- Bearish candle: #EF4444 (red)
- Wick: Gray
- MA(50): Blue
- MA(200): Purple
- RSI area: Cyan gradient

### 3.5 Table Component

**Structure:**
```
┌──────────────────────────────────────────┐
│ Header (sticky, background: #334155)     │
├──────────────────────────────────────────┤
│ Row 1 (hover: bg #475569)                │
├──────────────────────────────────────────┤
│ Row 2 (alt bg: #1E293B)                  │
├──────────────────────────────────────────┤
│ Pagination + Results count               │
└──────────────────────────────────────────┘
```

**Features:**
- Sticky header on scroll
- Sortable columns (indicator ▲▼)
- Hover rows highlight
- Alternating row colors
- Responsive: Horizontal scroll on mobile
- Cell padding: 12px
- Min row height: 36px

### 3.6 Button Component

**Padding:** 12px 20px  
**Border-radius:** 6px  
**Font-weight:** 600  
**Transition:** All 200ms  

**Variants:**
```
Primary (Blue):
  Normal: bg #2563EB, text white
  Hover: bg #1D4ED8 (darker), shadow up
  Active: opacity 0.9
  Disabled: opacity 0.5, cursor not-allowed

Secondary (Outline):
  Normal: border #2563EB, text #2563EB, bg transparent
  Hover: bg #2563EB, text white
  Active: opacity 0.9

Danger (Red):
  Normal: bg #EF4444, text white
  Hover: bg #DC2626 (darker)
  Active: opacity 0.9

Success (Green):
  Normal: bg #10B981, text white
  Hover: bg #059669 (darker)
  Active: opacity 0.9

Small: 8px 16px, 14px font
Medium: 12px 20px, 16px font (default)
Large: 16px 24px, 16px font (bold)
```

### 3.7 Input Component

**Padding:** 10px 12px  
**Border:** 1px solid #334155  
**Border-radius:** 6px  
**Background:** #0F172A  
**Font:** 14px, monospace for prices  

**States:**
- Normal: border #334155
- Focus: border #2563EB, outline 2px blue
- Error: border #EF4444, outline 2px red
- Disabled: opacity 0.5, cursor not-allowed

**Variants:**
- Text input
- Number input (right-aligned)
- Select dropdown
- Textarea
- Date/Time inputs

### 3.8 Toggle/Switch Component

**Width:** 44px  
**Height:** 24px  
**Border-radius:** 12px (fully rounded)  

**States:**
- Off: bg #334155, knob left
- On: bg #10B981, knob right
- Disabled: opacity 0.5
- Transition: 200ms smooth

### 3.9 Modal/Dialog Component

**Background:** Overlay 50% opacity black  
**Width:** 500px (responsive: 90% mobile, 80% tablet)  
**Border-radius:** 12px  
**Shadow:** Large (0 20px 25px)  
**Padding:** 24px  

**Structure:**
```
┌─────────────────────────┐
│ Title          [X]      │
├─────────────────────────┤
│ Content                 │
│                         │
├─────────────────────────┤
│ [Cancel]     [Action]   │
└─────────────────────────┘
```

### 3.10 Notification/Toast Component

**Position:** Top-right corner  
**Size:** 320px width  
**Padding:** 16px  
**Border-radius:** 8px  
**Auto-dismiss:** 5 seconds  
**Z-index:** 9999  

**Variants:**
- Success: Green bg, checkmark icon
- Error: Red bg, X icon
- Warning: Amber bg, ! icon
- Info: Blue bg, ⓘ icon

---

## 4. Page Specifications

### 4.1 Dashboard Page (`/`)

**Layout:** 3-column (Left: 25%, Center: 65%, Right: 10%)  

**Sections:**

#### Header (Full Width)
```
┌──────────────────────────────────────────────┐
│ Trading Dashboard                  1D 1W 1M  │
│ Real-time market analysis...                 │
└──────────────────────────────────────────────┘
```
- H1: "Trading Dashboard"
- Subtitle: "Real-time market analysis..."
- Time filter buttons (1D active)

#### Metrics Row (Full Width, 4 Columns)
```
Today's P&L    │ Win Rate   │ Active Pos  │ Risk Level
₹2,340.50      │ 68.5%      │ 3          │ Low
+12.3% port    │ 154 trades │ ₹245.2K    │ 1.2% of limit
```

#### Left Column (25%)
```
Market Status
- NIFTY: 23,500 (+2.3%)
- BANKNIFTY: 46,800 (+1.8%)
- FINNIFTY: 19,200 (+0.5%)

Active Signals (Card list)
- NIFTY-CALL 23500
  Entry: ₹45.50
  SL: ₹42.00
  Target: ₹52.00
  [Execute] [Details] [Save]
```

#### Center Column (65%)
```
Price Chart (Full height)
- Candlestick chart with MA200, MA50
- Volume bars
- Interval selector
- Legend

Trade History Table
- Columns: Time, Type, Entry, Exit, Qty, P&L
- Last 10 trades
- Sortable, filterable
```

#### Right Column (10%)
```
Key Indicators
- RSI: 58.2%
- MACD: -0.45
- Bollinger: 23,350-23,650
- PCR: 1.25
- VIX: 16.8
```

**Mobile:** Stack full-width, hide right column

### 4.2 Signals Page (`/signals`)

**Layout:** Full-width single column  

**Sections:**

#### Header
```
Trading Signals
AI-generated signals with backtesting results
[Run Backtest] [Export]
```

#### Filters
```
┌────────────────────────────────────────────┐
│ Symbol      Signal      Confidence  Range   │
│ [Dropdown]  [Dropdown]  [Dropdown]  [...]   │
│ [Clear Filters]    342 signals found      │
└────────────────────────────────────────────┘
```
- 4-column grid
- Dropdowns for each filter
- "Clear All" button
- Result count

#### Summary Stats (4-column)
```
Total Signals  │ Avg Confidence │ Win Rate  │ Avg Return
342 (+15%)     │ 72.4%          │ 68.5%     │ +2.34%
Last 24h       │ High quality   │ Above avg │ Risk-adj
```

#### Signals Table
```
View Toggle: [Table] [Cards]

Table:
Time    │ Symbol      │ Signal  │ Confidence │ Entry  │ Target │ SL    │ Status   │ Action
10:30   │ NIFTY-CALL  │ BUY ▲   │ 87%        │ 45.50  │ 52.00  │ 42.00 │ Executed │ [Edit]
10:15   │ NIFTY-CALL  │ SELL ▼  │ 76%        │ 48.20  │ 44.00  │ 51.00 │ Pending  │ [Edit]

Cards (Mobile):
[Card] [Card] [Card]
Per row: 1 (mobile), 2 (tablet), 3 (desktop)
```

#### Pattern Analysis
```
Chart showing:
- Signal types distribution (pie)
- Confidence distribution (histogram)
- Accuracy by pattern (bar chart)
- Model contribution (stacked bar)
```

### 4.3 Orders Page (`/orders`)

**Layout:** 2-column (Left: 40%, Right: 60%)  

**Sections:**

#### Pending Orders (Left)
```
BUY NIFTY 45,230
Qty: 100 | Status: ACTIVE
Entry: 45.50
Target: 52.00 | SL: 42.00
[Modify] [Cancel] [Close]

SELL BANKNIFTY 410
Qty: 50 | Status: PENDING
...
```

#### Order History (Right)
```
Timeline view:
10:45 - Order Filled
       BUY NIFTY 45,230 @ ₹45.50
       Qty: 100
       Commission: -₹50

10:30 - Order Placed
       SELL BANKNIFTY 410 @ ₹409.50
       ...
```

#### Order Details Modal
```
Order ID: ORD-20260227-001
Symbol: NIFTY50
Type: BUY CALL
Entry: 45.50
Target: 52.00
SL: 42.00
Quantity: 100
Status: OPEN
P&L: +₹150 (0.33% return)
Duration: 45 minutes
Commission: -₹50
[Modify] [Close] [Cancel]
```

### 4.4 Performance Page (`/performance`)

**Layout:** Full-width dashboard  

**KPIs (Top 4-column):**
```
Monthly P&L    │ Win Rate   │ Sharpe Ratio │ Max Drawdown
+₹45,600       │ 68.5%      │ 1.8          │ 12.5%
(+18.2% month) │ 154 trades │ (Excellent)  │ (Acceptable)
```

**Charts (2-column):**

Left:
```
P&L Over Time (Line chart)
- Cumulative line
- Daily bars below
- Range selector
```

Right:
```
Win/Loss Distribution (Pie chart)
- Winners: 68.5%
- Losers: 31.5%
- Click for details
```

**Trade Statistics (Tabbed):**

```
Tab 1: Daily Performance
Time      │ Trades │ Win  │ P&L      │ Win%   │ Return
2026-02-27│ 8     │ 6    │ +3,450   │ 75%    │ +2.3%
2026-02-26│ 12    │ 7    │ +1,850   │ 58.3%  │ +1.2%
2026-02-25│ 10    │ 7    │ +2,300   │ 70%    │ +1.8%

Tab 2: Weekly/Monthly
...

Tab 3: Trade Journal
Full trade log with detailed P&L
```

**Export Options:**
```
[Export CSV] [Export PDF] [Export Excel]
Period: [Month Selector]
```

### 4.5 Risk Management Page (`/risk`)

**Layout:** Full-width dashboard  

**Risk Gauges (4-column):**

Left:
```
Daily Loss (Gauge)
  -₹8,500 / -₹20,000 (42.5%)
  Status: SAFE (Green)
```

Center-Left:
```
Position Risk (Gauge)
  2.1% / 2.0% (105%)
  Status: WARNING (Amber)
```

Center-Right:
```
Leverage (Gauge)
  2.3x / 5x (46%)
  Status: SAFE (Green)
```

Right:
```
VaR (95%) (Gauge)
  ₹12,450 potential loss
  Status: INFO (Blue)
```

**Risk Matrix (Full Width):**
```
Correlation Matrix (Heatmap)
              NIFTY  BankNifty  FinNifty  Crude   Gas
NIFTY         1.00    0.85      0.72     -0.15   -0.08
BankNifty     0.85    1.00      0.68     -0.12   -0.05
FinNifty      0.72    0.68      1.00     -0.18   -0.10
Crude        -0.15   -0.12     -0.18      1.00    0.42
Gas          -0.08   -0.05     -0.10      0.42    1.00

(Green: Low correlation, Red: High correlation)
```

**Warnings (Alert List):**
```
⚠️  POSITION_RISK_HIGH
    Current: 2.1% of capital
    Action: Reduce position or close trade

ℹ️  CORRELATION_ALERT
    NIFTY + BankNifty correlation: 0.85
    Recommendation: Diversify
```

### 4.6 Settings Page (`/settings`)

**Layout:** 2-column (Left: 25% nav, Right: 75% content)  

**Left Navigation:**
```
Account
Trading Rules
Risk Limits
Notifications
API Keys
Appearance
```

**Account Section:**
```
Account Info
- ID: ACC-123456
- Created: Feb 20, 2026
- Role: Trader

Change Password
[Current] [New] [Confirm]
[Save]

Session Management
Active Sessions: 1
[View Details] [Logout All]
```

**Trading Rules:**
```
Auto-Execute: [Toggle ON]
  Execute trades on signal generation

Paper Trading: [Toggle OFF]
  Switch to live broker connection

Exit on Time: [Toggle ON]
  Duration: 5 hours
```

**Risk Limits:**
```
Daily Loss Limit: -₹20,000
Max Leverage: 5x
Max Position Size: 2% of capital
Max Correlation: 0.8
```

**Notifications:**
```
[Toggle] Signal Generated
[Toggle] Order Executed
[Toggle] Trade Closed
[Toggle] Risk Warning
[Toggle] System Alert

Email: user@example.com
Telegram: Connected ✓
Discord: Not Connected
```

**Appearance:**
```
Theme: [Light] [Dark] [Auto] (Dark selected)
Language: [English] [Hindi]
Timezone: IST (UTC+5:30)
Time Format: [24h] [12h] (24h selected)
Currency: [INR] [USD]
```

---

## 5. Interactions & Animations

### 5.1 Transitions

```css
Default: all 200ms ease-out
Fast: buttons, hovers (150ms)
Slow: modals, notifications (300ms)
```

### 5.2 Animations

#### Page Load
```
1. Navbar: Slide down 200ms
2. Metrics: Fade in + bounce 300ms (staggered 50ms)
3. Charts: Fade in 500ms
4. Tables: Slide up 400ms
```

#### Signal Notification
```
Toast:
1. Slide in from top-right (300ms)
2. Grow shadow effect
3. Stay for 5s
4. Slide out + fade (300ms)

Card pulse on new signal:
1. Glow effect 1s (repeats until dismissed)
2. Subtle scale 1.02 on hover
```

#### Trade Execution
```
Button:
1. On click: Ripple effect (200ms)
2. Loading: Spinner animation
3. Success: Green checkmark + popout (400ms)
4. Error: Shake animation + red glow (500ms)
```

### 5.3 Hover Effects

```css
Buttons: +10% brightness, shadow up
Cards: Border color change, shadow up
Links: Text color to primary, underline appear
Tables: Row bg highlight, 5% opacity increase
Inputs: Border color change, focus shadow
```

---

## 6. Accessibility (WCAG 2.1 AA)

### 6.1 Color Contrast
- Normal text: 4.5:1 (AAA)
- Large text: 3:1 (AA)
- UI components: 3:1

### 6.2 Keyboard Navigation
- Tab order: Logical (left to right, top to bottom)
- Focus indicators: 2px blue outline
- Skip-to-main: Available on page load
- Modal focus trap: Enabled

### 6.3 Screen Reader Support
```html
<button aria-label="Close modal" aria-pressed="false">
<div role="status" aria-live="assertive">Trade executed</div>
<table role="table">
  <thead role="rowgroup">
    <tr role="row">
      <th role="columnheader">Time</th>
    </tr>
  </thead>
</table>
```

### 6.4 Semantic HTML
- Use proper heading hierarchy (H1 → H6)
- List items for lists
- Form labels with inputs
- Landmark regions (nav, main, aside)

---

## 7. Dark Mode Implementation

### 7.1 CSS Variables

```css
:root {
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
  --bg-tertiary: #334155;
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --border-color: #334155;
  --success-color: #10B981;
  --danger-color: #EF4444;
}

@media (prefers-color-scheme: light) {
  :root {
    --bg-primary: #FFFFFF;
    --bg-secondary: #F1F5F9;
    --bg-tertiary: #E2E8F0;
    --text-primary: #0F172A;
    --text-secondary: #475569;
    --border-color: #CBD5E1;
  }
}
```

### 7.2 Toggle Implementation

```javascript
// Check system preference
const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

// Toggle button
function toggleTheme() {
  document.body.classList.toggle('light-mode');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// Apply saved preference on load
window.addEventListener('load', () => {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') document.body.classList.add('light-mode');
});
```

---

## 8. Responsive Design Strategy

### 8.1 Mobile-First Approach

```css
/* Mobile: 320px+ */
.card { width: 100%; padding: 12px; }
.grid { grid-template-columns: 1fr; }

/* Tablet: 768px+ */
@media (min-width: 768px) {
  .card { width: calc(50% - 12px); }
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .card { width: calc(25% - 18px); }
  .grid { grid-template-columns: repeat(4, 1fr); }
}
```

### 8.2 Breakpoint Reference

```
Mobile:  320px (iPhone 6/7/8)
Tablet:  768px (iPad)
Desktop: 1024px (MacBook Air)
Large:   1440px (27" display)
XL:      1920px (4K display)
```

### 8.3 Touch-Friendly Design

- Minimum tap target: 44x44px
- Spacing between buttons: 8px+
- No hover-only interactions
- Swipe gestures for tables (left/right)
- Fat-finger friendly form inputs

---

## 9. Performance Optimization

### 9.1 Image Optimization

```
- SVG for icons (prefer over PNG/JPG)
- WebP with PNG fallback
- Lazy load images below fold
- Responsive images (srcset)
- Compression: TinyPNG/ImageOptim
```

### 9.2 CSS Optimization

```
- CRITICAL CSS (above fold) inline
- Deferred CSS for below fold
- CSS Grid > Float layouts
- Hardware acceleration (transform, opacity)
- Avoid expensive properties (box-shadow, blur)
```

### 9.3 JavaScript Optimization

```
- Defer non-critical JS
- Bundle splitting (main, vendor, async)
- Minification + compression
- Lazy load heavy libraries
- Service Worker for offline support
```

---

## 10. Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | Full |
| Firefox | 88+ | Full |
| Safari | 14+ | Full |
| Edge | 90+ | Full |
| Mobile Safari | 14+ | Full |
| Chrome Android | 90+ | Full |

---

## 11. Design Tokens Summary

```
Colors:   Brand Blue (#2563EB), Accent Green (#10B981)
Spacing:  8px base unit (8, 16, 24, 32px)
Typography: Inter 16px base, JetBrains Mono for code
Shadows:  Subtle to Large (4 levels)
Radius:   8px (default), 4px (small), 12px (large)
Duration: 200ms (default), 150ms (fast), 300ms (slow)
```

