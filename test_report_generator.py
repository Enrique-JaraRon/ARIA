"""
Tests du module report_generator.py
"""

from hedging_analysis import calculate_delta_hedge
from portfolio import Portfolio
from pricing_BS import OptionContract
from report_generator import (
    generate_executive_risk_report,
    generate_pdf_report,
    generate_risk_report,
)
from risk_score import calculate_risk_score
from scenario_analysis import run_standard_scenarios
from var_analysis import calculate_var_es, parametric_var_estimate


def create_test_portfolio() -> Portfolio:
    """Cree un portefeuille simple pour tester le rapport."""

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


def build_report_inputs():
    """Prepare shared report inputs."""

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

    return {
        "portfolio": portfolio,
        "spot": 500,
        "volatility": 0.20,
        "alerts": [],
        "scenario_results": scenario_results,
        "var_result": var_result,
        "parametric_var": parametric_var,
        "hedge_result": hedge_result,
        "risk_score_result": risk_score_result,
        "market_snapshot": None,
        "llm_analysis": None,
    }


def test_generate_risk_report_returns_text():
    """Verifie que le rapport est bien genere sous forme de texte."""

    report = generate_risk_report(
        **build_report_inputs()
    )

    assert isinstance(
        report,
        str
    )

    assert len(report) > 0


def test_generate_risk_report_contains_executive_sections():
    """Verifie que le rapport contient les grandes sections attendues."""

    report = generate_risk_report(
        **build_report_inputs()
    )

    expected_sections = [
        "# ARIA - Rapport exécutif de risque",
        "Préparé par : **Enrique Jara Ron**",
        "## 1. Vue exécutive",
        "## 2. Diagnostic de risque",
        "## 3. Points clés",
        "## 4. Recommandations à étudier",
        "## 5. Avertissement",
        "## Annexe - chiffres significatifs",
        "| Indicateur | Valeur |",
    ]

    for section in expected_sections:
        assert section in report


def test_generate_risk_report_can_include_llm_analysis():
    """Verifie que l'analyse LLM peut etre incluse dans le rapport."""

    inputs = build_report_inputs()
    llm_analysis = (
        "Analyse test generee par le LLM."
    )
    inputs["llm_analysis"] = llm_analysis

    report = generate_risk_report(
        **inputs
    )

    assert "## 4. Recommandations à étudier" in report
    assert llm_analysis in report


def test_generate_executive_risk_report_alias_matches_main_report():
    """Verifie que l'alias explicite produit le meme rapport."""

    inputs = build_report_inputs()

    report = generate_risk_report(
        **inputs
    )
    executive_report = generate_executive_risk_report(
        **inputs
    )

    assert report.splitlines()[0] == executive_report.splitlines()[0]


def test_generate_pdf_report_returns_pdf_bytes():
    """Verifie que le rapport PDF est un vrai fichier PDF."""

    report = generate_risk_report(
        **build_report_inputs()
    )

    pdf_report = generate_pdf_report(
        report
    )

    assert isinstance(
        pdf_report,
        bytes
    )
    assert pdf_report.startswith(
        b"%PDF"
    )
    assert len(
        pdf_report
    ) > 1000
