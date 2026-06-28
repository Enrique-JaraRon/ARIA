"""
Tests du module report_generator.py
"""

from hedging_analysis import calculate_delta_hedge
from portfolio import Portfolio
from pricing_BS import OptionContract
from report_generator import generate_risk_report
from risk_score import calculate_risk_score
from scenario_analysis import run_standard_scenarios
from var_analysis import calculate_var_es, parametric_var_estimate


def create_test_portfolio() -> Portfolio:
    """Crée un portefeuille simple pour tester le rapport."""

    portfolio = Portfolio(
        name="Test Report"
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

    put = OptionContract(
        S=500,
        K=470,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="put",
        q=0.0
    )

    portfolio.add_option(
        contract=call,
        quantity=10,
        multiplier=100,
        name="Calls test"
    )

    portfolio.add_option(
        contract=put,
        quantity=-5,
        multiplier=100,
        name="Puts test"
    )

    return portfolio


def test_generate_risk_report_returns_text():
    """Vérifie que le rapport est bien généré sous forme de texte."""

    portfolio = create_test_portfolio()

    scenario_results = run_standard_scenarios(
        portfolio
    )

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500
    )

    parametric_var = parametric_var_estimate(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1
    )

    hedge_result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=500
    )

    risk_score_result = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenario_results,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20
    )

    report = generate_risk_report(
        portfolio=portfolio,
        spot=500,
        volatility=0.20,
        alerts=[],
        scenario_results=scenario_results,
        var_result=var_result,
        parametric_var=parametric_var,
        hedge_result=hedge_result,
        risk_score_result=risk_score_result,
        market_snapshot=None,
        llm_analysis=None
    )

    assert isinstance(
        report,
        str
    )

    assert len(report) > 0


def test_generate_risk_report_contains_main_sections():
    """Vérifie que le rapport contient les grandes sections attendues."""

    portfolio = create_test_portfolio()

    scenario_results = run_standard_scenarios(
        portfolio
    )

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500
    )

    parametric_var = parametric_var_estimate(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1
    )

    hedge_result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=500
    )

    risk_score_result = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenario_results,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20
    )

    report = generate_risk_report(
        portfolio=portfolio,
        spot=500,
        volatility=0.20,
        alerts=[],
        scenario_results=scenario_results,
        var_result=var_result,
        parametric_var=parametric_var,
        hedge_result=hedge_result,
        risk_score_result=risk_score_result,
        market_snapshot=None,
        llm_analysis=None
    )

    assert "# Rapport de risque ARIA" in report
    assert "## Résumé général" in report
    assert "## Risk Score ARIA" in report
    assert "## Greeks du portefeuille" in report
    assert "## Couverture delta indicative" in report
    assert "## Stress tests" in report
    assert "## VaR / Expected Shortfall" in report
    assert "## Alertes quantitatives" in report
    assert "## Positions du portefeuille" in report


def test_generate_risk_report_can_include_llm_analysis():
    """Vérifie que l'analyse LLM peut être incluse dans le rapport."""

    portfolio = create_test_portfolio()

    scenario_results = run_standard_scenarios(
        portfolio
    )

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=500
    )

    parametric_var = parametric_var_estimate(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1
    )

    hedge_result = calculate_delta_hedge(
        portfolio=portfolio,
        current_spot=500
    )

    risk_score_result = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenario_results,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20
    )

    llm_analysis = (
        "Analyse test générée par le LLM."
    )

    report = generate_risk_report(
        portfolio=portfolio,
        spot=500,
        volatility=0.20,
        alerts=[],
        scenario_results=scenario_results,
        var_result=var_result,
        parametric_var=parametric_var,
        hedge_result=hedge_result,
        risk_score_result=risk_score_result,
        market_snapshot=None,
        llm_analysis=llm_analysis
    )

    assert "## Analyse LLM" in report
    assert llm_analysis in report
