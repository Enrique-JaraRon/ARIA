"""
Tests du module risk_score.py
"""

from portfolio_engine.portfolio import Portfolio
from portfolio_engine.pricing_BS import OptionContract
from risk_engine.risk_score import calculate_risk_score
from risk_engine.scenario_analysis import run_standard_scenarios
from risk_engine.var_analysis import calculate_var_es


def create_test_portfolio() -> Portfolio:
    """Crée un portefeuille simple pour les tests."""

    portfolio = Portfolio(
        name="Test Risk Score"
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


def test_risk_score_is_between_0_and_100():
    """Vérifie que le score est bien compris entre 0 et 100."""

    portfolio = create_test_portfolio()

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500
    )

    scenario_results = run_standard_scenarios(
        portfolio
    )

    result = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenario_results,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20
    )

    assert result.score >= 0
    assert result.score <= 100
    assert isinstance(
        result.label,
        str
    )
    assert isinstance(
        result.explanation,
        str
    )
    assert isinstance(
        result.main_drivers,
        list
    )


def test_risk_score_has_at_least_one_driver():
    """Vérifie que le score renvoie au moins une explication."""

    portfolio = create_test_portfolio()

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500
    )

    scenario_results = run_standard_scenarios(
        portfolio
    )

    result = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenario_results,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20
    )

    assert len(result.main_drivers) >= 1


def test_risk_score_distinguishes_low_and_high_risk_portfolios():
    """Le score doit varier selon le niveau de risque du portefeuille."""

    low_risk = Portfolio(name="Faible risque")
    low_risk.add_stock(
        spot=100,
        quantity=10,
        name="ETF diversifie",
        underlying="VTI",
    )

    high_risk = create_test_portfolio()

    low_var, _ = calculate_var_es(
        portfolio=low_risk,
        annual_volatility=0.08,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500,
    )
    high_var, _ = calculate_var_es(
        portfolio=high_risk,
        annual_volatility=0.30,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500,
    )

    low_score = calculate_risk_score(
        portfolio=low_risk,
        alerts=[],
        var_result=low_var,
        scenario_results=run_standard_scenarios(low_risk),
        delta_limit=100,
        gamma_limit=10,
        vega_limit=100,
    )
    high_score = calculate_risk_score(
        portfolio=high_risk,
        alerts=[],
        var_result=high_var,
        scenario_results=run_standard_scenarios(high_risk),
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20,
    )

    assert low_score.score < high_score.score
    assert high_score.score < 100
