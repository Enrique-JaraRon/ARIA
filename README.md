# ARIA — Portfolio Risk & Options Analytics

[![ARIA Tests](https://github.com/Enrique-JaraRon/ARIA/actions/workflows/tests.yml/badge.svg)](https://github.com/Enrique-JaraRon/ARIA/actions/workflows/tests.yml)

**An interactive Python and Streamlit application for options pricing, portfolio sensitivities and market-risk analysis.**

ARIA brings together **Black–Scholes pricing, implied volatility, Greeks, Value-at-Risk (VaR), Expected Shortfall (ES), Monte Carlo analysis, scenario stress tests and PDF reporting** in a single portfolio workflow.

**Author:** Enrique Jara Ron · Financial Engineering (ESILV) · Applied Economics (Université Paris-Dauphine – PSL)

## At a glance

| Capability | Implementation |
| --- | --- |
| **Options pricing** | European calls/puts under Black–Scholes; implied-volatility solver; put–call parity checks |
| **Sensitivities** | Delta, Gamma, Theta, Vega, Rho, Vanna and Volga; spot/volatility risk surfaces |
| **Portfolio risk** | VaR, Expected Shortfall, Monte Carlo analysis, P&L profiles, exposures and correlations |
| **Stress scenarios** | Historical and custom shocks; visual comparison of stressed portfolio outcomes |
| **Reporting** | Interactive Streamlit dashboards and generated PDF risk reports |
| **Code quality** | Modular pricing/risk layers, Pytest tests, Ruff and GitHub Actions CI |

## Application preview

<details open>
<summary><strong>Portfolio and risk dashboards</strong></summary>

![Portfolio editor](screenshots/portfolio_editor.png)

![Risk dashboard](screenshots/dashboard.png)

</details>

<details>
<summary><strong>More screenshots: stress tests, VaR, Greeks and reporting</strong></summary>

**Stress testing**

![Stress testing](screenshots/stress_testing.png)

**VaR and Expected Shortfall**

![VaR and ES](screenshots/var_analysis.png)

**Greeks**

![Greeks profile](screenshots/greeks_profile.png)

**Spot / volatility risk matrix**

![Risk matrix](screenshots/risk_matrix.png)

**P&L sensitivities**

![PnL sensitivities](screenshots/sensitivities_pnl.png)

**Probabilistic risk**

![Probabilistic risk](screenshots/probabilistic_risk.png)

**PDF report preview**

![Risk report](screenshots/risk_report.png)

</details>

## Quick start

Requires **Python 3.11+**. The commands below work in a shell from the repository root.

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

**Windows PowerShell** (using the venv directly; no activation required):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

### Run quality checks

```bash
python -m pytest -q
python -m ruff check .
```

The repository also includes an automated [test workflow](.github/workflows/tests.yml). A successful CI run indicates the configured checks passed on that commit; it does not constitute independent validation of every risk-model assumption.

## Quantitative methods

**Derivatives**
- Black–Scholes European option pricing and implied-volatility inversion.
- Standard and higher-order Greeks for examining local sensitivities.
- Spot/volatility scenario grids and option P&L profiles.

**Risk and portfolio analytics**
- VaR / Expected Shortfall calculations and Monte Carlo simulation.
- Historical/custom stress analysis and correlation/volatility diagnostics.
- Portfolio aggregation and risk-oriented visual reporting.

**Engineering focus**
- Separate pricing, portfolio and risk modules.
- Testable quantitative functions and a dedicated application layer.
- Configuration via environment variables rather than hard-coded credentials.

The intended workflow is to **load or define a portfolio → value instruments → calculate risk and sensitivities → stress positions → review/export a report**.

## Code structure

```text
ARIA/
├── app/                 # Workflow, UI components, reports and optional LLM integration
├── portfolio_engine/    # Instruments, pricing, portfolios and market data
├── risk_engine/         # VaR, stress tests, Greeks, P&L and risk analysis
├── tests/               # Automated quantitative and application checks
├── tools/               # Development diagnostics
├── scripts/             # Local start/quality utilities
├── screenshots/         # Application previews
└── streamlit_app.py     # Streamlit entry point
```

Key files include [Black–Scholes pricing](portfolio_engine/pricing_BS.py), [market data](portfolio_engine/market_data.py), [VaR analysis](risk_engine/var_analysis.py) and [scenario analysis](risk_engine/scenario_analysis.py).

## Market data and optional commentary

ARIA supports manual portfolio inputs and local/external market-data workflows for prices, returns, volatility and correlation estimates. Reproducibility depends on the selected data source, observation window and instrument assumptions.

An **optional LLM module** can generate natural-language risk commentary. It is separate from the numerical engines. To configure it locally:

```powershell
Copy-Item .env.example .env
```

Supply any required API key through the local `.env` or environment variables; **never commit credentials**. The application can be explored without claiming that LLM-generated explanations constitute validated quantitative output.

For deployment-specific notes, see [Streamlit Cloud guidance](STREAMLIT_CLOUD_DEPLOYMENT.md).

## Limitations and next steps

- Black–Scholes uses simplifying assumptions such as constant volatility and a stylised underlying-price process.
- VaR, ES and stress-test outputs are conditional on the data, model choices and specified scenarios; they do not describe every tail event.
- Monte Carlo estimates can vary with simulation settings, and historical risk estimates may be unstable across regimes.
- Future development could include richer volatility dynamics, additional products and more detailed risk attribution.

This is an **educational financial-engineering project**, not a live trading system, audited risk engine or source of investment advice.
