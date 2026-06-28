"""
ARIA - Génération de rapport de risque
"""

from datetime import datetime
from typing import Any

from portfolio import Portfolio


def format_number(
    value: float,
    decimals: int = 2
) -> str:
    """Formate un nombre de manière lisible."""

    return f"{value:,.{decimals}f}"


def format_percent(
    value: float,
    decimals: int = 2
) -> str:
    """Formate un pourcentage de manière lisible."""

    return f"{value:.{decimals}%}"


def generate_positions_section(
    portfolio: Portfolio
) -> str:
    """Génère la section des positions."""

    lines = []

    lines.append(
        "## Positions du portefeuille\n"
    )

    if not portfolio.positions:
        lines.append(
            "Aucune position dans le portefeuille.\n"
        )

        return "\n".join(
            lines
        )

    lines.append(
        "| Nom | Instrument | Quantité | Multiplicateur | Strike | Maturité | Valeur |"
    )

    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|"
    )

    for position in portfolio.positions:

        if hasattr(
            position,
            "contract"
        ):

            contract = position.contract

            lines.append(
                "| "
                f"{position.name} | "
                f"{contract.option_type.upper()} | "
                f"{position.quantity} | "
                f"{position.multiplier} | "
                f"{format_number(contract.K)} | "
                f"{format_number(contract.T, 3)} | "
                f"{format_number(position.market_value())} |"
            )

        else:
            lines.append(
                "| "
                f"{position.name} | "
                "ACTION | "
                f"{position.quantity} | "
                "1 | "
                "- | "
                "- | "
                f"{format_number(position.market_value())} |"
            )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_greeks_section(
    portfolio: Portfolio
) -> str:
    """Génère la section des Greeks."""

    greeks = portfolio.total_greeks()

    lines = []

    lines.append(
        "## Greeks du portefeuille\n"
    )

    lines.append(
        "| Greek | Valeur |"
    )

    lines.append(
        "|---|---:|"
    )

    for greek_name in [
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "vanna",
        "volga"
    ]:

        lines.append(
            f"| {greek_name.capitalize()} | "
            f"{format_number(greeks[greek_name], 6)} |"
        )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_stress_section(
    scenario_results: list[Any]
) -> str:
    """Génère la section des stress tests."""

    lines = []

    lines.append(
        "## Stress tests\n"
    )

    if not scenario_results:
        lines.append(
            "Aucun stress test disponible.\n"
        )

        return "\n".join(
            lines
        )

    lines.append(
        "| Scénario | Variation spot | Variation volatilité | P&L |"
    )

    lines.append(
        "|---|---:|---:|---:|"
    )

    for result in scenario_results:

        lines.append(
            "| "
            f"{result.name} | "
            f"{format_percent(result.spot_change_percent)} | "
            f"{format_percent(result.volatility_change_points)} | "
            f"{format_number(result.profit_and_loss)} |"
        )

    worst_scenario = min(
        scenario_results,
        key=lambda result: result.profit_and_loss
    )

    best_scenario = max(
        scenario_results,
        key=lambda result: result.profit_and_loss
    )

    lines.append(
        ""
    )

    lines.append(
        f"Meilleur scénario : **{best_scenario.name}** "
        f"avec un P&L de **{format_number(best_scenario.profit_and_loss)}**."
    )

    lines.append(
        f"Pire scénario : **{worst_scenario.name}** "
        f"avec un P&L de **{format_number(worst_scenario.profit_and_loss)}**."
    )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_alerts_section(
    alerts: list[Any]
) -> str:
    """Génère la section des alertes."""

    lines = []

    lines.append(
        "## Alertes quantitatives\n"
    )

    if not alerts:
        lines.append(
            "Aucune anomalie détectée.\n"
        )

        return "\n".join(
            lines
        )

    for alert in alerts:

        lines.append(
            f"- **{alert.severity} — {alert.name}** : "
            f"{alert.message}"
        )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_var_section(
    var_result: Any,
    parametric_var: float
) -> str:
    """Génère la section VaR / Expected Shortfall."""

    lines = []

    lines.append(
        "## VaR / Expected Shortfall\n"
    )

    lines.append(
        "| Mesure | Valeur |"
    )

    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Niveau de confiance | "
        f"{format_percent(var_result.confidence_level)} |"
    )

    lines.append(
        f"| Horizon | "
        f"{var_result.horizon_days} jour(s) |"
    )

    lines.append(
        f"| Nombre de simulations | "
        f"{var_result.number_of_simulations} |"
    )

    lines.append(
        f"| VaR | "
        f"{format_number(var_result.var_amount)} |"
    )

    lines.append(
        f"| Expected Shortfall | "
        f"{format_number(var_result.expected_shortfall)} |"
    )

    lines.append(
        f"| Pire perte simulée | "
        f"{format_number(var_result.worst_loss)} |"
    )

    lines.append(
        f"| VaR paramétrique | "
        f"{format_number(parametric_var)} |"
    )

    lines.append(
        ""
    )

    lines.append(
        "La VaR estime une perte maximale sur un horizon donné "
        "avec un certain niveau de confiance. "
        "L'Expected Shortfall mesure la perte moyenne dans les pires scénarios."
    )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_hedge_section(
    hedge_result: Any
) -> str:
    """Génère la section de couverture delta."""

    lines = []

    lines.append(
        "## Couverture delta indicative\n"
    )

    if hedge_result.hedge_quantity > 0:
        action = "Acheter du sous-jacent"

    elif hedge_result.hedge_quantity < 0:
        action = "Vendre du sous-jacent"

    else:
        action = "Ne rien faire"

    lines.append(
        "| Mesure | Valeur |"
    )

    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Delta actuel | "
        f"{format_number(hedge_result.current_delta, 6)} |"
    )

    lines.append(
        f"| Action indicative | "
        f"{action} |"
    )

    lines.append(
        f"| Quantité de couverture | "
        f"{format_number(abs(hedge_result.hedge_quantity), 0)} |"
    )

    lines.append(
        f"| Valeur de couverture | "
        f"{format_number(hedge_result.hedge_market_value)} |"
    )

    lines.append(
        f"| Delta après couverture | "
        f"{format_number(hedge_result.hedged_delta, 6)} |"
    )

    lines.append(
        ""
    )

    lines.append(
        hedge_result.explanation
    )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_risk_score_section(
    risk_score_result: Any
) -> str:
    """Génère la section du Risk Score ARIA."""

    lines = []

    lines.append(
        "## Risk Score ARIA\n"
    )

    lines.append(
        f"Score : **{risk_score_result.score}/100**"
    )

    lines.append(
        f"Niveau : **{risk_score_result.label}**"
    )

    lines.append(
        ""
    )

    lines.append(
        risk_score_result.explanation
    )

    lines.append(
        ""
    )

    lines.append(
        "Principaux facteurs de risque :"
    )

    for driver in risk_score_result.main_drivers:
        lines.append(
            f"- {driver}"
        )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_market_section(
    market_snapshot: Any | None
) -> str:
    """Génère la section des données de marché."""

    lines = []

    lines.append(
        "## Données de marché\n"
    )

    if market_snapshot is None:
        lines.append(
            "Aucune donnée de marché externe utilisée.\n"
        )

        return "\n".join(
            lines
        )

    lines.append(
        "| Donnée | Valeur |"
    )

    lines.append(
        "|---|---:|"
    )

    lines.append(
        f"| Ticker | {market_snapshot.ticker} |"
    )

    lines.append(
        f"| Dernier prix | {format_number(market_snapshot.last_price)} |"
    )

    lines.append(
        f"| Prix précédent | {format_number(market_snapshot.previous_price)} |"
    )

    lines.append(
        f"| Rendement journalier | {format_percent(market_snapshot.daily_return)} |"
    )

    lines.append(
        f"| Volatilité historique annualisée | "
        f"{format_percent(market_snapshot.annualized_volatility)} |"
    )

    lines.append(
        f"| Nombre d'observations | {market_snapshot.number_of_observations} |"
    )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_risk_report(
    portfolio: Portfolio,
    spot: float,
    volatility: float,
    alerts: list[Any],
    scenario_results: list[Any],
    var_result: Any,
    parametric_var: float,
    hedge_result: Any,
    risk_score_result: Any,
    market_snapshot: Any | None = None,
    llm_analysis: str | None = None
) -> str:
    """
    Génère un rapport complet de risque au format Markdown.
    """

    report_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    lines = []

    lines.append(
        "# Rapport de risque ARIA"
    )

    lines.append(
        ""
    )

    lines.append(
        f"Date de génération : **{report_date}**"
    )

    lines.append(
        ""
    )

    lines.append(
        "## Résumé général\n"
    )

    lines.append(
        f"Valeur du portefeuille : **{format_number(portfolio.total_market_value())}**"
    )

    lines.append(
        f"Spot utilisé : **{format_number(spot)}**"
    )

    lines.append(
        f"Volatilité utilisée : **{format_percent(volatility)}**"
    )

    lines.append(
        f"Nombre de positions : **{len(portfolio.positions)}**"
    )

    lines.append(
        ""
    )

    lines.append(
        generate_market_section(
            market_snapshot
        )
    )

    lines.append(
        generate_risk_score_section(
            risk_score_result
        )
    )

    lines.append(
        generate_greeks_section(
            portfolio
        )
    )

    lines.append(
        generate_hedge_section(
            hedge_result
        )
    )

    lines.append(
        generate_stress_section(
            scenario_results
        )
    )

    lines.append(
        generate_var_section(
            var_result,
            parametric_var
        )
    )

    lines.append(
        generate_alerts_section(
            alerts
        )
    )

    lines.append(
        generate_positions_section(
            portfolio
        )
    )

    if llm_analysis:

        lines.append(
            "## Analyse LLM\n"
        )

        lines.append(
            llm_analysis
        )

        lines.append(
            ""
        )

    lines.append(
        "## Limites\n"
    )

    lines.append(
        "Ce rapport est généré automatiquement par ARIA. "
        "Il repose sur des hypothèses simplifiées, notamment Black-Scholes, "
        "des stress tests prédéfinis et une VaR Monte Carlo simplifiée. "
        "Il ne constitue pas un conseil financier."
    )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


if __name__ == "__main__":
    from hedging_analysis import calculate_delta_hedge
    from pricing_BS import OptionContract
    from risk_score import calculate_risk_score
    from scenario_analysis import run_standard_scenarios
    from var_analysis import calculate_var_es, parametric_var_estimate

    portfolio = Portfolio(
        name="Test rapport"
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
        quantity=20,
        multiplier=100,
        name="Calls achetés"
    )

    scenarios = run_standard_scenarios(
        portfolio
    )

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=1000
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
        scenario_results=scenarios,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20
    )

    report = generate_risk_report(
        portfolio=portfolio,
        spot=500,
        volatility=0.20,
        alerts=[],
        scenario_results=scenarios,
        var_result=var_result,
        parametric_var=parametric_var,
        hedge_result=hedge_result,
        risk_score_result=risk_score_result
    )

    print(report)
