"""
Tests du module var_analysis.py
"""

from portfolio_engine.portfolio import Portfolio
from portfolio_engine.pricing_BS import OptionContract
from risk_engine.var_analysis import calculate_var_es, parametric_var_estimate


def create_test_portfolio() -> Portfolio:
    """Crée un portefeuille simple pour les tests."""

    portfolio = Portfolio(
        name="Test VaR"
    )

    call = OptionContract(
        S=500,
        K=500,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="call",
        q=0.0
    )

    portfolio.add_option(
        contract=call,
        quantity=10,
        multiplier=100,
        name="Calls test"
    )

    return portfolio


def test_calculate_var_es_returns_valid_result():
    """Vérifie que la VaR et l'Expected Shortfall sont calculés."""

    portfolio = create_test_portfolio()

    result, simulations = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500
    )

    assert result.confidence_level == 0.95
    assert result.horizon_days == 1
    assert result.number_of_simulations == 500
    assert result.var_amount >= 0
    assert result.expected_shortfall >= 0
    assert len(simulations) == 500

    assert "Profit / Perte" in simulations.columns
    assert "Perte" in simulations.columns
    assert "Rendement spot" in simulations.columns


def test_parametric_var_estimate_is_positive():
    """Vérifie que la VaR paramétrique est positive ou nulle."""

    portfolio = create_test_portfolio()

    var_estimate = parametric_var_estimate(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1
    )

    assert var_estimate >= 0
