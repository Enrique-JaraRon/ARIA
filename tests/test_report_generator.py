"""
Tests du module report_generator.py
"""

import pandas as pd

from app.report_generator import (
    compact_llm_commentary,
    generate_executive_risk_report,
    generate_pdf_report,
    generate_professional_pdf_report,
    generate_report_preview,
    generate_risk_report,
)
from portfolio_engine.market_data import HistoricalMarketData, MarketSnapshot
from portfolio_engine.portfolio import Portfolio
from portfolio_engine.pricing_BS import OptionContract
from risk_engine.hedging_analysis import calculate_delta_hedge
from risk_engine.risk_score import calculate_risk_score
from risk_engine.scenario_analysis import run_standard_scenarios
from risk_engine.var_analysis import calculate_var_es, parametric_var_estimate


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
        "## 1. Explication simple pour le client",
        "## 2. Vue exécutive",
        "## 3. Diagnostic de risque",
        "## 4. Points clés",
        "## 5. Recommandations à étudier",
        "## 6. Avertissement",
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

    assert "## 5. Recommandations à étudier" in report
    assert llm_analysis in report


def test_generate_risk_report_cleans_compact_llm_markdown():
    """Verifie que les sous-parties LLM compactes passent a la ligne."""

    inputs = build_report_inputs()
    inputs["llm_analysis"] = (
        "3. Actions recommandees a etudier "
        "a) Couverture delta immediate - vendre. "
        "b) Reduction de convexite - transformer."
    )

    report = generate_risk_report(
        **inputs
    )

    assert "etudier\n\na)" in report
    assert "vendre.\n\nb)" in report


def test_compact_llm_commentary_removes_excessive_spacing():
    """Verifie que l'affichage LLM reste compact dans Streamlit et le PDF."""

    raw_commentary = (
        "1. Diagnostic synthetique\n\n\n\n"
        "- Risque principal : delta eleve.\n\n\n\n\n"
        "a) Couverture delta immediate\n\n\n"
        "- Vendre une partie du sous-jacent."
    )

    compact = compact_llm_commentary(
        raw_commentary,
        language="fr",
    )

    assert "\n\n\n" not in compact
    assert "Lecture qualitative LLM" in compact
    assert "delta eleve" in compact


def test_generate_risk_report_accepts_non_string_llm_payload():
    """Verifie qu'un retour LLM non standard ne fait pas planter le rapport."""

    inputs = build_report_inputs()
    inputs["llm_analysis"] = {
        "message": "Analyse structuree"
    }

    report = generate_risk_report(
        **inputs
    )

    assert "Analyse structuree" in report


def build_test_market_history() -> HistoricalMarketData:
    """Prepare un historique marche multi-sous-jacents pour le PDF premium."""

    dates = pd.date_range(
        "2025-01-01",
        periods=6,
        freq="B"
    )
    prices = pd.DataFrame(
        {
            "SPY": [
                500,
                505,
                502,
                510,
                514,
                518,
            ],
            "QQQ": [
                420,
                424,
                421,
                428,
                432,
                436,
            ],
        },
        index=dates,
    )
    returns = prices.pct_change(
        fill_method=None
    ).dropna()
    snapshots = {
        "SPY": MarketSnapshot(
            ticker="SPY",
            last_price=518,
            previous_price=514,
            daily_return=518 / 514 - 1,
            annualized_volatility=0.18,
            number_of_observations=6,
            source="Test",
            status="OK",
        ),
        "QQQ": MarketSnapshot(
            ticker="QQQ",
            last_price=436,
            previous_price=432,
            daily_return=436 / 432 - 1,
            annualized_volatility=0.22,
            number_of_observations=6,
            source="Test",
            status="OK",
        ),
    }

    return HistoricalMarketData(
        tickers=[
            "SPY",
            "QQQ",
        ],
        prices=prices,
        returns=returns,
        snapshots=snapshots,
        failed_tickers={},
        source="Test",
        status="OK",
        timestamp="2026-07-03T00:00:00+00:00",
    )


def test_generate_risk_report_supports_english_language():
    """Verifie que le rapport Markdown peut etre genere en anglais."""

    report = generate_risk_report(
        **build_report_inputs(),
        language="en",
    )

    assert "# ARIA - Executive Risk Report" in report
    assert "## 1. Plain-language client explanation" in report
    assert "Prepared by: **Enrique Jara Ron**" in report
    assert "Rapport exécutif" not in report


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


def test_generate_report_preview_is_short_and_actionable():
    """Verifie que l'aperçu telechargeable reste une synthese professionnelle."""

    inputs = build_report_inputs()
    preview = generate_report_preview(
        portfolio=inputs["portfolio"],
        scenario_results=inputs["scenario_results"],
        var_result=inputs["var_result"],
        probabilistic_result=None,
        hedge_result=inputs["hedge_result"],
        risk_score_result=inputs["risk_score_result"],
        llm_analysis="Diagnostic : surveiller le delta. Action : tester une couverture.",
        language="fr",
    )

    assert "ARIA - Apercu analyste" in preview
    assert "Score ARIA" in preview
    assert "Lecture prioritaire" in preview
    assert len(
        preview.splitlines()
    ) < 35


def test_generate_professional_pdf_report_accepts_market_history():
    """Verifie que le PDF premium integre un historique multi-sous-jacents."""

    inputs = build_report_inputs()
    pdf_report = generate_professional_pdf_report(
        **inputs,
        market_history=build_test_market_history(),
        language="fr",
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
    ) > 4000
