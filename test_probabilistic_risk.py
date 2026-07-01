"""Tests for probabilistic_risk.py."""

import numpy as np
import pandas as pd
import pytest

from portfolio import Portfolio
from pricing_BS import OptionContract
from probabilistic_risk import (
    build_probabilistic_risk_report_text,
    contribution_table,
    probabilistic_metrics_table,
    simulate_probabilistic_risk,
)


def create_probabilistic_test_portfolio() -> Portfolio:
    """Create a simple multi-underlying portfolio."""

    portfolio = Portfolio(name="Probabilistic test")

    aapl_call = OptionContract(
        S=180,
        K=185,
        T=0.35,
        r=0.04,
        sigma=0.28,
        option_type="call",
        q=0.0,
    )
    nvda_put = OptionContract(
        S=125,
        K=115,
        T=0.30,
        r=0.04,
        sigma=0.45,
        option_type="put",
        q=0.0,
    )

    portfolio.add_stock(
        spot=180,
        quantity=25,
        name="AAPL shares",
        underlying="AAPL",
    )
    portfolio.add_option(
        contract=aapl_call,
        quantity=4,
        multiplier=100,
        name="AAPL calls",
        underlying="AAPL",
    )
    portfolio.add_option(
        contract=nvda_put,
        quantity=-2,
        multiplier=100,
        name="NVDA short puts",
        underlying="NVDA",
    )

    return portfolio


def test_simulation_returns_requested_number_of_rows():
    portfolio = create_probabilistic_test_portfolio()

    result, simulations = simulate_probabilistic_risk(
        portfolio=portfolio,
        horizon_days=21,
        number_of_simulations=1000,
        confidence_level=0.95,
        seed=7,
    )

    assert result.number_of_simulations == 1000
    assert len(simulations) == 1000
    assert "Portfolio return" in simulations.columns
    assert "Portfolio P&L" in simulations.columns


def test_loss_probabilities_are_between_zero_and_one():
    portfolio = create_probabilistic_test_portfolio()

    result, _ = simulate_probabilistic_risk(
        portfolio=portfolio,
        number_of_simulations=1000,
        confidence_level=0.95,
        seed=11,
    )

    probabilities = [
        result.probability_of_loss,
        result.probability_loss_gt_5,
        result.probability_loss_gt_10,
        result.probability_loss_gt_20,
    ]

    assert all(0 <= probability <= 1 for probability in probabilities)


def test_var_and_expected_shortfall_match_distribution():
    portfolio = create_probabilistic_test_portfolio()

    result, simulations = simulate_probabilistic_risk(
        portfolio=portfolio,
        horizon_days=21,
        number_of_simulations=3000,
        confidence_level=0.95,
        seed=13,
    )

    returns = simulations["Portfolio return"].to_numpy()
    expected_var_95 = np.quantile(returns, 0.05)
    tail_returns = returns[returns <= expected_var_95]

    assert result.var_95 == pytest.approx(expected_var_95)
    assert result.expected_shortfall_95 == pytest.approx(tail_returns.mean())
    assert result.expected_shortfall_95 <= result.var_95


def test_module_handles_simple_stock_portfolio():
    portfolio = Portfolio(name="Simple stock")
    portfolio.add_stock(
        spot=100,
        quantity=10,
        name="SPY stock",
        underlying="SPY",
    )

    result, simulations = simulate_probabilistic_risk(
        portfolio=portfolio,
        horizon_days=5,
        number_of_simulations=500,
        confidence_level=0.99,
        seed=21,
    )

    assert len(simulations) == 500
    assert result.var_99 <= result.var_95
    assert result.expected_shortfall_99 <= result.var_99


def test_risk_contributions_are_coherent():
    portfolio = create_probabilistic_test_portfolio()

    result, _ = simulate_probabilistic_risk(
        portfolio=portfolio,
        horizon_days=21,
        number_of_simulations=2000,
        confidence_level=0.95,
        seed=31,
    )

    contributors = contribution_table(result)

    assert not contributors.empty
    assert contributors["Contribution %"].between(0, 1).all()
    assert contributors["Contribution %"].sum() == pytest.approx(1.0)
    assert result.main_risk_driver != "Not available"


def test_historical_returns_drive_underlying_columns_without_llm():
    portfolio = create_probabilistic_test_portfolio()
    dates = pd.date_range("2025-01-01", periods=30, freq="B")
    historical_returns = pd.DataFrame(
        {
            "AAPL": np.linspace(-0.01, 0.012, len(dates)),
            "NVDA": np.linspace(0.018, -0.015, len(dates)),
        },
        index=dates,
    )

    result, simulations = simulate_probabilistic_risk(
        portfolio=portfolio,
        historical_returns=historical_returns,
        horizon_days=10,
        number_of_simulations=1000,
        confidence_level=0.95,
        seed=41,
    )

    assert "AAPL return" in simulations.columns
    assert "NVDA return" in simulations.columns
    assert 0 <= result.probability_of_loss <= 1


def test_metrics_table_and_report_text_use_computed_numbers():
    portfolio = create_probabilistic_test_portfolio()

    result, _ = simulate_probabilistic_risk(
        portfolio=portfolio,
        number_of_simulations=1000,
        confidence_level=0.95,
        seed=51,
    )

    metrics = probabilistic_metrics_table(result)
    report_text = build_probabilistic_risk_report_text(
        probability_of_loss=result.probability_of_loss,
        var_95=result.var_95,
        expected_shortfall_95=result.expected_shortfall_95,
        main_driver=result.main_risk_driver,
    )

    assert "Probability of loss" in metrics["Metric"].tolist()
    assert f"{result.probability_of_loss:.1%}" in report_text
    assert f"{result.var_95:.1%}" in report_text
    assert result.main_risk_driver in report_text
    assert "predictions certaines" in report_text
