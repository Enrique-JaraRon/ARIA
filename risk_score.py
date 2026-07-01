"""
ARIA - Score de risque global.
"""

from dataclasses import dataclass
from typing import Any

from portfolio import OptionPosition, Portfolio, StockPosition
from var_analysis import VarResult


@dataclass
class RiskScoreResult:
    """Résultat du score de risque ARIA."""

    score: int
    label: str
    explanation: str
    main_drivers: list[str]


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Force une valeur à rester dans un intervalle."""

    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


def _alert_penalty(
    alerts: list[Any],
) -> tuple[float, list[str]]:
    """Calcule la pénalité liée aux alertes."""

    penalty = 0.0
    drivers = []

    for alert in alerts:
        severity = str(
            getattr(
                alert,
                "severity",
                "",
            )
        ).upper()
        name = getattr(
            alert,
            "name",
            "Alerte",
        )

        if severity == "CRITIQUE":
            penalty += 10
            drivers.append(f"Alerte critique : {name}")
        elif severity in {"ÉLEVÉE", "ELEVEE", "Ã‰LEVÃ‰E"}:
            penalty += 7
            drivers.append(f"Alerte élevée : {name}")
        else:
            penalty += 4
            drivers.append(f"Alerte modérée : {name}")

    return _clamp(penalty, 0, 20), drivers


def _var_penalty(
    var_result: VarResult,
) -> tuple[float, list[str]]:
    """Calcule la pénalité liée à la VaR et à l'Expected Shortfall."""

    drivers = []
    portfolio_value = abs(var_result.portfolio_value)

    if portfolio_value <= 0:
        return 0.0, drivers

    var_ratio = var_result.var_amount / portfolio_value
    es_ratio = var_result.expected_shortfall / portfolio_value

    penalty = 0.0
    penalty += _clamp(var_ratio * 90, 0, 18)
    penalty += _clamp(es_ratio * 70, 0, 14)

    if var_ratio > 0.10:
        drivers.append("VaR élevée par rapport à la valeur du portefeuille")

    if es_ratio > 0.15:
        drivers.append("Expected Shortfall élevé dans les pires scénarios")

    return _clamp(penalty, 0, 28), drivers


def _stress_penalty(
    scenario_results: list[Any],
    portfolio_value: float,
) -> tuple[float, list[str]]:
    """Calcule la pénalité liée aux stress tests."""

    drivers = []

    if not scenario_results:
        return 0.0, drivers

    absolute_portfolio_value = abs(portfolio_value)

    if absolute_portfolio_value <= 0:
        return 0.0, drivers

    worst_pnl = min(
        result.profit_and_loss
        for result in scenario_results
    )
    worst_loss = max(-worst_pnl, 0)
    loss_ratio = worst_loss / absolute_portfolio_value

    penalty = _clamp(loss_ratio * 85, 0, 24)

    if loss_ratio > 0.10:
        drivers.append("Perte importante dans le pire scénario de stress")

    return penalty, drivers


def _greeks_penalty(
    portfolio: Portfolio,
    delta_limit: float,
    gamma_limit: float,
    vega_limit: float,
) -> tuple[float, list[str]]:
    """Calcule la pénalité liée aux Greeks."""

    drivers = []
    greeks = portfolio.total_greeks()
    penalty = 0.0

    if delta_limit > 0:
        delta_ratio = abs(greeks["delta"]) / delta_limit
        penalty += _clamp(delta_ratio * 5, 0, 8)

        if delta_ratio > 1:
            drivers.append("Delta supérieur à la limite définie")

    if gamma_limit > 0:
        gamma_ratio = abs(greeks["gamma"]) / gamma_limit
        penalty += _clamp(gamma_ratio * 5, 0, 8)

        if gamma_ratio > 1:
            drivers.append("Gamma supérieur à la limite définie")

    if vega_limit > 0:
        vega_ratio = abs(greeks["vega"]) / vega_limit
        penalty += _clamp(vega_ratio * 5, 0, 8)

        if vega_ratio > 1:
            drivers.append("Vega supérieure à la limite définie")

    return _clamp(penalty, 0, 22), drivers


def _composition_penalty(
    portfolio: Portfolio,
) -> tuple[float, list[str]]:
    """Ajoute concentration, diversification et complexité instrumentale."""

    if not portfolio.positions:
        return 0.0, ["Aucune position dans le portefeuille"]

    market_values = [
        abs(position.market_value())
        for position in portfolio.positions
    ]
    gross_value = sum(market_values)

    if gross_value <= 0:
        return 0.0, ["Valeur brute insuffisante pour mesurer la concentration"]

    weights = [
        value / gross_value
        for value in market_values
    ]
    top_weight = max(weights)
    underlyings = {
        getattr(
            position,
            "underlying",
            getattr(position, "name", "Inconnu"),
        )
        for position in portfolio.positions
    }
    option_weight = sum(
        value
        for value, position in zip(
            market_values,
            portfolio.positions,
            strict=False,
        )
        if isinstance(position, OptionPosition)
    ) / gross_value
    stock_weight = sum(
        value
        for value, position in zip(
            market_values,
            portfolio.positions,
            strict=False,
        )
        if isinstance(position, StockPosition)
    ) / gross_value

    penalty = 0.0
    drivers = []

    if top_weight > 0.45:
        penalty += min((top_weight - 0.45) * 35, 12)
        drivers.append(
            f"Concentration élevée sur une position ({top_weight:.1%} de l'exposition brute)"
        )

    if len(underlyings) <= 2:
        penalty += 6
        drivers.append("Diversification limitée entre sous-jacents")

    if option_weight > 0.50:
        penalty += 7
        drivers.append("Poids important des options dans l'exposition brute")
    elif stock_weight > 0.90 and len(underlyings) <= 3:
        penalty += 4
        drivers.append("Portefeuille actions concentré sur peu de sous-jacents")

    return _clamp(penalty, 0, 20), drivers


def calculate_risk_score(
    portfolio: Portfolio,
    alerts: list[Any],
    var_result: VarResult,
    scenario_results: list[Any],
    delta_limit: float,
    gamma_limit: float,
    vega_limit: float,
) -> RiskScoreResult:
    """
    Calcule un score de risque global entre 0 et 100.

    Le score combine les Greeks, alertes, VaR, Expected Shortfall, stress tests,
    concentration et diversification. Les composantes sont plafonnées pour
    éviter un score artificiellement bloqué à 100/100.
    """

    greeks_score, greeks_drivers = _greeks_penalty(
        portfolio=portfolio,
        delta_limit=delta_limit,
        gamma_limit=gamma_limit,
        vega_limit=vega_limit,
    )
    alert_score, alert_drivers = _alert_penalty(alerts)
    var_score, var_drivers = _var_penalty(var_result)
    stress_score, stress_drivers = _stress_penalty(
        scenario_results=scenario_results,
        portfolio_value=portfolio.total_market_value(),
    )
    composition_score, composition_drivers = _composition_penalty(portfolio)

    score = int(
        round(
            _clamp(
                greeks_score
                + alert_score
                + var_score
                + stress_score
                + composition_score,
                0,
                100,
            )
        )
    )

    drivers = [
        *greeks_drivers,
        *alert_drivers,
        *var_drivers,
        *stress_drivers,
        *composition_drivers,
    ]

    if score < 25:
        label = "Risque faible"
        explanation = (
            "Le portefeuille présente peu de signaux de risque avec les données disponibles."
        )
    elif score < 50:
        label = "Risque modéré"
        explanation = (
            "Le portefeuille présente un risque modéré : certains facteurs doivent être suivis."
        )
    elif score < 75:
        label = "Risque élevé"
        explanation = "Le portefeuille présente plusieurs facteurs de risque importants."
    else:
        label = "Risque très élevé"
        explanation = (
            "Le portefeuille combine concentration, stress ou sensibilités importantes."
        )

    if not drivers:
        drivers.append("Aucun facteur de risque majeur détecté")

    return RiskScoreResult(
        score=score,
        label=label,
        explanation=explanation,
        main_drivers=drivers[:6],
    )


if __name__ == "__main__":
    from pricing_BS import OptionContract
    from scenario_analysis import run_standard_scenarios
    from var_analysis import calculate_var_es

    portfolio = Portfolio(name="Test Risk Score")

    call = OptionContract(
        S=500,
        K=500,
        T=0.25,
        r=0.05,
        sigma=0.20,
        option_type="call",
        q=0.0,
    )

    portfolio.add_option(
        contract=call,
        quantity=20,
        multiplier=100,
        name="Calls achetés",
    )

    var_result, _ = calculate_var_es(
        portfolio=portfolio,
        annual_volatility=0.20,
        confidence_level=0.95,
        horizon_days=1,
        number_of_simulations=1000,
    )

    scenarios = run_standard_scenarios(portfolio)

    result = calculate_risk_score(
        portfolio=portfolio,
        alerts=[],
        var_result=var_result,
        scenario_results=scenarios,
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20,
    )

    print("Score de risque ARIA")
    print(f"Score : {result.score}/100")
    print(f"Niveau : {result.label}")
    print(result.explanation)
    print(result.main_drivers)
