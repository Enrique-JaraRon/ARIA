
"""
ARIA - Workflow principal
"""

import os

from dotenv import load_dotenv

from anomaly_detector import AnomalyDetector, create_snapshot
from llm_explainer import LLMExplainer
from portfolio import OptionPosition, Portfolio, StockPosition
from pricing_BS import OptionContract
from risk_history import RiskHistory


def update_portfolio_market(
    portfolio: Portfolio,
    spot: float,
    implied_volatility: float
) -> None:
    """Met à jour le spot et la volatilité du portefeuille."""

    for position in portfolio.positions:

        if isinstance(position, OptionPosition):
            position.contract.S = spot
            position.contract.sigma = implied_volatility

        elif isinstance(position, StockPosition):
            position.spot = spot


def build_demo_portfolio() -> Portfolio:
    """Crée un portefeuille simple pour tester ARIA."""

    portfolio = Portfolio(
        name="Portefeuille ARIA"
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
        quantity=20,
        name="Calls achetés"
    )

    portfolio.add_option(
        contract=put,
        quantity=-10,
        name="Puts vendus"
    )

    portfolio.add_stock(
        spot=500,
        quantity=-5,
        name="Couverture en actions"
    )

    return portfolio


def generate_llm_analysis(
    snapshot,
    alerts,
    risk_score_result=None,
    scenario_results=None,
    var_result=None,
    probabilistic_result=None,
    hedge_result=None,
    market_snapshot=None,
    language: str = "fr"
) -> str:
    """Demande au LLM d'expliquer les alertes détectées."""

    load_dotenv()

    model = os.getenv("ARIA_LLM_MODEL")

    if not model:
        if language.lower() == "en":
            if not alerts:
                return (
                    "### ARIA Summary\n\n"
                    "No major quantitative anomaly was detected. "
                    "The portfolio should still be monitored through its Greeks, "
                    "VaR, Expected Shortfall and stress tests. "
                    "This reading relies on simplified ARIA model assumptions and "
                    "is not personalized financial advice."
                )

            return (
                "The LLM model is not configured. "
                "Add the ARIA_LLM_MODEL environment variable."
            )

        if not alerts:
            return (
                "### Synthèse ARIA\n\n"
                "Aucune anomalie quantitative majeure n'a été détectée. "
                "Le portefeuille doit néanmoins être suivi sur ses Greeks, "
                "sa VaR, son Expected Shortfall et ses stress tests. "
                "Cette lecture repose sur les hypothèses simplifiées du "
                "modèle ARIA et ne constitue pas un conseil financier."
            )

        return (
            "Le modèle LLM n'est pas défini. "
            "Ajoute la variable ARIA_LLM_MODEL."
        )

    try:
        explainer = LLMExplainer(
            model=model
        )

        return explainer.explain(
            snapshot=snapshot,
            alerts=alerts,
            risk_score_result=risk_score_result,
            scenario_results=scenario_results,
            var_result=var_result,
            probabilistic_result=probabilistic_result,
            hedge_result=hedge_result,
            market_snapshot=market_snapshot,
            language=language
        )

    except Exception as error:
        return (
            "Impossible de générer l'analyse LLM.\n"
            f"Erreur : {error}"
        )


def run_aria(
    current_spot: float,
    current_volatility: float
) -> None:
    """Lance le workflow complet d'ARIA."""

    portfolio = build_demo_portfolio()

    update_portfolio_market(
        portfolio=portfolio,
        spot=current_spot,
        implied_volatility=current_volatility
    )

    current_snapshot = create_snapshot(
        portfolio=portfolio,
        spot=current_spot,
        implied_volatility=current_volatility
    )

    history_manager = RiskHistory(
        file_path="data/risk_history.csv"
    )

    history = history_manager.load_snapshots()

    previous_snapshot = (
        history[-1]
        if history
        else None
    )

    detector = AnomalyDetector(
        delta_limit=10.0,
        gamma_limit=1.0,
        vega_limit=20.0,
        daily_spot_move_limit=0.03,
        volatility_move_limit=0.05,
        z_score_limit=2.5
    )

    alerts = detector.detect_all(
        current=current_snapshot,
        history=history,
        previous=previous_snapshot
    )

    portfolio.summary()

    print("\nÉtat actuel du marché")
    print(f"Spot : {current_spot}")
    print(
        f"Volatilité implicite : "
        f"{current_volatility:.2%}"
    )

    print("\nAlertes quantitatives")

    if not alerts:
        print("Aucune anomalie détectée.")

    else:
        print(
            f"{len(alerts)} anomalie(s) détectée(s)."
        )

        for alert in alerts:
            alert.display()

    print("\nAnalyse du LLM")

    llm_analysis = generate_llm_analysis(
        snapshot=current_snapshot,
        alerts=alerts
    )

    print(llm_analysis)

    history_manager.save_snapshot(
        current_snapshot
    )

    print(
        "\nLe snapshot actuel a été sauvegardé "
        "dans data/risk_history.csv."
    )


if __name__ == "__main__":

    # Modifie ces valeurs pour simuler une situation de marché
    current_spot = 465
    current_volatility = 0.32

    run_aria(
        current_spot=current_spot,
        current_volatility=current_volatility
    )

