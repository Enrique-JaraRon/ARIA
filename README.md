# ARIA — Adaptive Risk Intelligence & Analytics

> **Portfolio risk, derivatives and scenario analytics platform built for quantitative finance applications.**

ARIA is a Python/Streamlit platform designed to turn a portfolio of equities, ETFs and options into a structured risk analysis. It combines **derivatives pricing, Greeks, Value-at-Risk, Expected Shortfall, Monte Carlo simulation, stress testing and market-data analytics** in a single interactive application.

Developed by **Enrique Jara Ron**, Financial Engineering student at ESILV with a background in Applied Economics from Université Paris-Dauphine – PSL.

> Educational and research project. Outputs are not investment advice and do not guarantee future performance.

---

## Why ARIA?

The objective of ARIA is to bridge **quantitative models** and **practical portfolio decision-making**.

A user can build or import a portfolio, analyse its market exposures, run deterministic and probabilistic stress scenarios, inspect option sensitivities and generate an executive risk report.

### Core capabilities

- **Portfolio analytics** for equities, ETFs and options
- **Black-Scholes pricing** for European options
- **Implied volatility** and option sensitivity analysis
- **Greeks:** Delta, Gamma, Theta, Vega, Rho, Vanna and Volga
- **Value-at-Risk (VaR)** and **Expected Shortfall (ES)**
- **Monte Carlo risk simulation**
- Historical and custom **stress testing**
- Spot / volatility stress matrices
- P&L sensitivity analysis
- Historical market-data analysis
- Annualised volatility and correlation matrices
- Quantitative risk alerts
- Optional LLM-generated commentary
- Professional PDF risk reporting
- French / English interface

---

## Application Preview

### Portfolio Dashboard

![Portfolio dashboard](screenshots/portfolio_editor.png)

### Risk Dashboard

![ARIA risk dashboard](screenshots/dashboard.png)

### Stress Testing

![Stress testing](screenshots/stress_testing.png)

### Spot / Volatility Risk Matrix

![Risk matrix](screenshots/risk_matrix.png)

### VaR & Expected Shortfall

![VaR and Expected Shortfall](screenshots/var_analysis.png)

### P&L Sensitivities

![PnL sensitivities](screenshots/sensitivities_pnl.png)

### Greeks Profile

![Greeks profile](screenshots/greeks_profile.png)

### Probabilistic Risk

![Probabilistic risk](screenshots/probabilistic_risk.png)

### Executive Risk Report

![Risk report](screenshots/risk_report.png)

---

## Quantitative Methods

ARIA currently integrates several concepts commonly used in derivatives and market-risk analysis.

| Area | Methods |
|---|---|
| **Option Pricing** | Black-Scholes, European calls & puts |
| **Volatility** | Historical volatility, implied volatility |
| **Greeks** | Delta, Gamma, Theta, Vega, Rho, Vanna, Volga |
| **Market Risk** | VaR, Expected Shortfall |
| **Simulation** | Monte Carlo |
| **Scenario Analysis** | Historical shocks, custom stress scenarios |
| **Portfolio Analytics** | P&L profiles, correlations, exposure analysis |
| **Risk Monitoring** | Quantitative alerts and risk scoring |

---

## Market Data

ARIA can operate in manual mode for stable offline demonstrations or use external/local market data for more realistic analysis.

The market-data engine can build:

- price histories by underlying;
- daily returns;
- annualised volatility estimates;
- correlation matrices;
- inputs for probabilistic risk calibration.

Example CSV format:

```csv
Date,Ticker,Close
2026-01-02,SPY,500.0
2026-01-02,QQQ,430.0
2026-01-03,SPY,504.0
2026-01-03,QQQ,435.0
```

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

The project separates the **portfolio/pricing layer**, **risk engine** and **user interface** so that quantitative components can be tested independently from the application layer.

---

## Tech Stack

**Language**

- Python

**Quantitative & Data**

- NumPy
- Pandas
- SciPy
- Statistical and numerical methods

**Application**

- Streamlit

**Engineering**

- Pytest
- Ruff
- Modular Python architecture
- Environment-variable based configuration

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

## Optional LLM Layer

The quantitative engine works independently of any language model.

To enable the optional natural-language risk commentary, create a local `.env` file from `.env.example`.

```powershell
Copy-Item .env.example .env
```

Example:

```text
OPENAI_API_KEY=your_key_here
ARIA_LLM_MODEL=gpt-5-mini
```

---

## Quality Controls

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run linting:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

---

## Project Focus

ARIA is part of my work at the intersection of:

- **Quantitative Finance**
- **Derivatives**
- **Market Risk**
- **Portfolio Analytics**
- **Financial Engineering**
- **Python for Finance**

Future extensions may include additional pricing models, richer volatility modelling, more advanced portfolio-risk decomposition and further derivatives analytics.

---

## Author

**Enrique Jara Ron**

Financial Engineering — ESILV  
Applied Economics — Université Paris-Dauphine – PSL

GitHub: [Enrique-JaraRon](https://github.com/Enrique-JaraRon)
