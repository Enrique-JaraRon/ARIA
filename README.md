# ARIA — Adaptive Risk Intelligence & Analytics

> **A quantitative portfolio-risk and derivatives analytics platform built in Python and Streamlit.**

ARIA turns a portfolio of equities, ETFs and European options into a structured market-risk analysis. The project combines **derivatives pricing, Greeks, implied volatility, Value-at-Risk, Expected Shortfall, Monte Carlo simulation and stress testing** in one interactive application.

Built by **Enrique Jara Ron** — Financial Engineering student at **ESILV**, with a BSc in Applied Economics from **Université Paris-Dauphine – PSL**.

---

## At a glance

| Area | Implementation |
|---|---|
| **Derivatives** | Black-Scholes pricing, implied volatility, European calls & puts |
| **Greeks** | Delta, Gamma, Theta, Vega, Rho, Vanna, Volga |
| **Market Risk** | VaR, Expected Shortfall, risk alerts |
| **Simulation** | Monte Carlo portfolio-risk simulation |
| **Stress Testing** | Historical scenarios, custom shocks, spot/volatility matrices |
| **Portfolio Analytics** | P&L profiles, exposures, correlations, volatility |
| **Reporting** | Interactive dashboards and PDF risk reports |
| **Engineering** | Modular Python architecture, Pytest, Ruff, Streamlit |

### What this project demonstrates

- translating quantitative-finance concepts into usable analytical tools;
- implementing option-pricing and market-risk methods in Python;
- separating pricing, portfolio and risk logic into testable modules;
- designing an interactive workflow for portfolio and derivatives analysis;
- combining numerical methods, financial modelling and software engineering.

---

## Application preview

### Portfolio dashboard

![Portfolio dashboard](screenshots/portfolio_editor.png)

### Risk dashboard

![ARIA risk dashboard](screenshots/dashboard.png)

### Stress testing

![Stress testing](screenshots/stress_testing.png)

### Spot / volatility risk matrix

![Risk matrix](screenshots/risk_matrix.png)

### VaR & Expected Shortfall

![VaR and Expected Shortfall](screenshots/var_analysis.png)

### P&L sensitivities

![PnL sensitivities](screenshots/sensitivities_pnl.png)

### Greeks profile

![Greeks profile](screenshots/greeks_profile.png)

### Probabilistic risk

![Probabilistic risk](screenshots/probabilistic_risk.png)

### Executive risk report

![Risk report](screenshots/risk_report.png)

---

## Quantitative framework

ARIA currently integrates several methods commonly used in derivatives and market-risk analysis.

### Option pricing

- Black-Scholes pricing for European calls and puts
- put-call parity controls
- implied-volatility estimation
- spot and volatility sensitivity analysis

### Greeks

- Delta
- Gamma
- Theta
- Vega
- Rho
- Vanna
- Volga

### Market risk

- Value-at-Risk
- Expected Shortfall
- Monte Carlo simulation
- historical and custom stress scenarios
- P&L sensitivity analysis
- volatility and correlation analysis

---

## Architecture

```text
ARIA/
├── app/                # UI, configuration, LLM and reporting
├── portfolio_engine/   # Instruments, portfolio logic, pricing and market data
├── risk_engine/        # Stress tests, VaR, Greeks, probabilities and risk score
├── tests/              # Unit tests and quantitative controls
├── tools/              # Diagnostics and quality-control utilities
├── scripts/            # Local launch scripts
├── screenshots/        # Application screenshots
└── streamlit_app.py    # Main Streamlit entry point
```

The architecture separates the **portfolio/pricing layer**, **risk engine** and **user interface**, allowing quantitative components to be tested independently from the application layer.

---

## Tech stack

**Core:** Python

**Quantitative & data:** NumPy · Pandas · SciPy

**Application:** Streamlit

**Engineering:** Pytest · Ruff · modular Python architecture · environment-variable configuration

---

## Market data

ARIA can operate with manually supplied inputs for reproducible demonstrations or with external/local market data for more realistic analysis.

The market-data layer can build:

- historical prices by underlying;
- daily returns;
- annualised volatility estimates;
- correlation matrices;
- calibration inputs for probabilistic risk analysis.

Example CSV:

```csv
Date,Ticker,Close
2026-01-02,SPY,500.0
2026-01-02,QQQ,430.0
2026-01-03,SPY,504.0
2026-01-03,QQQ,435.0
```

---

## Installation

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Launch ARIA

```powershell
streamlit run streamlit_app.py
```

---

## Optional LLM layer

The quantitative engine works independently of any language model.

To enable optional natural-language risk commentary, create a local `.env` file from `.env.example`.

```powershell
Copy-Item .env.example .env
```

Example:

```text
OPENAI_API_KEY=your_key_here
ARIA_LLM_MODEL=gpt-5-mini
```

---

## Quality controls

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run linting:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

---

## Current focus

ARIA sits at the intersection of:

**Quantitative Finance · Derivatives · Market Risk · Portfolio Analytics · Financial Engineering · Python**

Possible extensions include richer volatility modelling, additional pricing methods, portfolio-risk decomposition and further derivatives analytics.

---

## Author

**Enrique Jara Ron**  
Financial Engineering — ESILV  
BSc Applied Economics — Université Paris-Dauphine – PSL

GitHub: [Enrique-JaraRon](https://github.com/Enrique-JaraRon)

> Educational and research project. Outputs are not investment advice and do not guarantee future performance.
