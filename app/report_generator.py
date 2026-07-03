"""
ARIA - Executive risk report generation.
"""

from datetime import datetime
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from portfolio_engine.portfolio import Portfolio

AUTHOR_NAME = "Enrique Jara Ron"

SCENARIO_LABELS = {
    "2008 Global Financial Crisis": {
        "fr": "Crise financière mondiale 2008",
        "en": "2008 Global Financial Crisis",
    },
    "Covid Liquidity Shock": {
        "fr": "Choc de liquidité Covid",
        "en": "Covid Liquidity Shock",
    },
    "Japan / Yen Carry Unwind": {
        "fr": "Crise japonaise / yen carry trade",
        "en": "Japan / Yen Carry Unwind",
    },
    "Inflation Shock": {
        "fr": "Choc inflationniste",
        "en": "Inflation Shock",
    },
    "Rates Shock": {
        "fr": "Choc de taux",
        "en": "Rates Shock",
    },
    "Tech Sell-off": {
        "fr": "Vente massive sur la tech",
        "en": "Tech Sell-off",
    },
    "Volatility Spike": {
        "fr": "Pic de volatilité",
        "en": "Volatility Spike",
    },
    "Sovereign / Banking Stress": {
        "fr": "Stress souverain / bancaire",
        "en": "Sovereign / Banking Stress",
    },
    "Hausse modérée": {
        "fr": "Hausse modérée",
        "en": "Moderate Rally",
    },
    "Stress de marché": {
        "fr": "Stress de marché",
        "en": "Market Stress",
    },
    "Scenario personnalise": {
        "fr": "Scénario personnalisé",
        "en": "Custom Scenario",
    },
}

RISK_LABELS_EN = {
    "Risque faible": "Low risk",
    "Risque modéré": "Moderate risk",
    "Risque eleve": "High risk",
    "Risque élevé": "High risk",
    "Risque très élevé": "Very high risk",
    "Risque critique": "Critical risk",
}


def format_number(
    value: float,
    decimals: int = 2
) -> str:
    """Format a number for a Markdown risk report."""

    return f"{value:,.{decimals}f}"


def format_percent(
    value: float,
    decimals: int = 2
) -> str:
    """Format a decimal value as a percentage."""

    return f"{value:.{decimals}%}"


def _market_value(
    value: Any,
    default: str = "N/A"
) -> str:
    """Return a readable market-data value."""

    if value is None:
        return default

    return str(
        value
    )


def _scenario_extremes(
    scenario_results: list[Any]
) -> tuple[Any | None, Any | None]:
    """Return best and worst stress scenarios."""

    if not scenario_results:
        return None, None

    best_scenario = max(
        scenario_results,
        key=lambda result: result.profit_and_loss
    )
    worst_scenario = min(
        scenario_results,
        key=lambda result: result.profit_and_loss
    )

    return best_scenario, worst_scenario


def _localized_scenario_name(
    name: str,
    language: str
) -> str:
    """Return a localized scenario label."""

    return SCENARIO_LABELS.get(
        str(name),
        {},
    ).get(
        language,
        str(name),
    )


def _localized_risk_label(
    label: str,
    language: str
) -> str:
    """Return a localized risk-score label."""

    if language == "en":
        return RISK_LABELS_EN.get(
            str(label),
            str(label),
        )

    return str(label)


def _localized_risk_explanation(
    score: int,
    explanation: str,
    language: str
) -> str:
    """Return a localized risk-score explanation."""

    if language == "fr":
        return explanation

    if score >= 80:
        return "The portfolio combines important concentration, stress losses or sensitivities."
    if score >= 60:
        return "The portfolio carries material risk and should be monitored before increasing exposure."
    if score >= 30:
        return "The portfolio has moderate risk and remains usable with active monitoring."
    return "The portfolio risk appears contained under the selected assumptions."


def _plain_language_client_commentary(
    portfolio: Portfolio,
    scenario_results: list[Any],
    var_result: Any,
    risk_score_result: Any,
    probabilistic_result: Any | None,
    language: str
) -> str:
    """Explain the report in simple words for a non-specialist client."""

    _, worst_scenario = _scenario_extremes(
        scenario_results
    )
    risk_label = _localized_risk_label(
        risk_score_result.label,
        language
    )
    worst_text = (
        _localized_scenario_name(
            worst_scenario.name,
            language
        )
        if worst_scenario is not None
        else ("non disponible" if language == "fr" else "not available")
    )

    if language == "en":
        probability_sentence = (
            f" The Monte Carlo model estimates a probability of loss of "
            f"{format_percent(probabilistic_result.probability_of_loss)}."
            if probabilistic_result is not None
            else ""
        )
        return (
            f"In simple terms, this portfolio is worth about "
            f"{format_number(portfolio.total_market_value())} and ARIA gives it "
            f"a risk score of {risk_score_result.score}/100 ({risk_label}). "
            f"The most adverse stress scenario is {worst_text}, while the VaR "
            f"is {format_number(var_result.var_amount)} and Expected Shortfall "
            f"is {format_number(var_result.expected_shortfall)}.{probability_sentence} "
            "This does not mean these losses will happen; it means they are "
            "useful warning levels. The practical next step is to check which "
            "positions create the largest downside, reduce or hedge them if the "
            "risk is too high, and then rerun the analysis before making a real "
            "decision."
        )

    probability_sentence = (
        f" Le modèle Monte Carlo estime une probabilité de perte de "
        f"{format_percent(probabilistic_result.probability_of_loss)}."
        if probabilistic_result is not None
        else ""
    )
    return (
        f"En termes simples, ce portefeuille vaut environ "
        f"{format_number(portfolio.total_market_value())} et ARIA lui attribue "
        f"un score de risque de {risk_score_result.score}/100 ({risk_label}). "
        f"Le scénario de stress le plus défavorable est {worst_text}. La VaR "
        f"ressort à {format_number(var_result.var_amount)} et l'Expected "
        f"Shortfall à {format_number(var_result.expected_shortfall)}.{probability_sentence} "
        "Cela ne veut pas dire que ces pertes vont arriver; ce sont des niveaux "
        "d'alerte pour mieux piloter le portefeuille. Concrètement, il faut "
        "regarder quelles lignes créent le plus de perte potentielle, réduire "
        "ou couvrir ces expositions si le risque est trop élevé, puis relancer "
        "l'analyse avant toute décision réelle."
    )


def _localized_probabilistic_interpretation(
    probabilistic_result: Any,
    language: str
) -> str:
    """Return a localized Monte Carlo interpretation."""

    if language == "fr":
        return probabilistic_result.interpretation

    return (
        "Monte Carlo read: under the selected assumptions, the portfolio has "
        f"an estimated probability of loss of "
        f"{format_percent(probabilistic_result.probability_of_loss)}. "
        f"The 95% VaR is {format_percent(probabilistic_result.var_95)}: 95% "
        "of simulated scenarios perform better than this threshold over the "
        f"selected horizon. The 95% Expected Shortfall is "
        f"{format_percent(probabilistic_result.expected_shortfall_95)}: in "
        "the worst 5% of simulated scenarios, the average loss is close to "
        f"that level. The main risk driver is "
        f"{probabilistic_result.main_risk_driver}. This is a risk-management "
        "view, not a certain forecast."
    )


def generate_executive_summary_section(
    portfolio: Portfolio,
    spot: float,
    volatility: float,
    alerts: list[Any],
    scenario_results: list[Any],
    var_result: Any,
    risk_score_result: Any
) -> str:
    """Generate the executive summary."""

    best_scenario, worst_scenario = _scenario_extremes(
        scenario_results
    )

    lines = [
        "## Executive Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Portfolio value | {format_number(portfolio.total_market_value())} |",
        f"| Spot used | {format_number(spot)} |",
        f"| Volatility used | {format_percent(volatility)} |",
        f"| Number of positions | {len(portfolio.positions)} |",
        f"| ARIA Risk Score | {risk_score_result.score}/100 - {_localized_risk_label(risk_score_result.label, 'en')} |",
        f"| Quantitative alerts | {len(alerts)} |",
        f"| VaR | {format_number(var_result.var_amount)} |",
        f"| Expected Shortfall | {format_number(var_result.expected_shortfall)} |",
    ]

    if worst_scenario is not None:
        lines.append(
            f"| Worst stress scenario | {_localized_scenario_name(worst_scenario.name, 'en')} "
            f"({format_number(worst_scenario.profit_and_loss)}) |"
        )

    if best_scenario is not None:
        lines.append(
            f"| Best stress scenario | {_localized_scenario_name(best_scenario.name, 'en')} "
            f"({format_number(best_scenario.profit_and_loss)}) |"
        )

    lines.extend(
        [
            "",
            (
                "This report summarizes risk metrics computed by ARIA. "
                "It is intended for risk review and monitoring, not as "
                "personalized investment advice."
            ),
            "",
        ]
    )

    return "\n".join(
        lines
    )


def generate_market_section(
    market_snapshot: Any | None
) -> str:
    """Generate the market context section."""

    lines = [
        "## Market Context",
        "",
    ]

    if market_snapshot is None:
        lines.extend(
            [
                "No external market data snapshot was used.",
                "",
            ]
        )
        return "\n".join(
            lines
        )

    lines.extend(
        [
            "| Data | Value |",
            "|---|---:|",
            f"| Source | {_market_value(getattr(market_snapshot, 'source', None))} |",
            f"| Status | {_market_value(getattr(market_snapshot, 'status', None))} |",
            f"| Ticker | {market_snapshot.ticker} |",
            f"| Last price | {format_number(market_snapshot.last_price)} |",
            f"| Previous price | {format_number(market_snapshot.previous_price)} |",
            f"| Daily return | {format_percent(market_snapshot.daily_return)} |",
            (
                "| Historical annualized volatility | "
                f"{format_percent(market_snapshot.annualized_volatility)} |"
            ),
            (
                "| Number of observations | "
                f"{market_snapshot.number_of_observations} |"
            ),
            f"| Timestamp | {_market_value(getattr(market_snapshot, 'timestamp', None))} |",
            "",
        ]
    )

    return "\n".join(
        lines
    )


def generate_positions_table(
    portfolio: Portfolio
) -> str:
    """Generate a Markdown table of portfolio positions."""

    if not portfolio.positions:
        return "No position in the portfolio.\n"

    lines = [
        "| Name | Instrument | Quantity | Multiplier | Strike | Maturity | Value |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

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
                "STOCK | "
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


def generate_portfolio_overview_section(
    portfolio: Portfolio
) -> str:
    """Generate the portfolio overview section."""

    return "\n".join(
        [
            "## Portfolio Overview",
            "",
            generate_positions_table(
                portfolio
            ),
        ]
    )


def generate_risk_score_section(
    risk_score_result: Any
) -> str:
    """Generate the risk score interpretation section."""

    lines = [
        "## Risk Score Interpretation",
        "",
        f"**Score:** {risk_score_result.score}/100",
        "",
        f"**Status:** {_localized_risk_label(risk_score_result.label, 'en')}",
        "",
        _localized_risk_explanation(
            risk_score_result.score,
            risk_score_result.explanation,
            "en",
        ),
        "",
        (
            "The ARIA Risk Score combines Greek limit breaches, "
            "quantitative alerts, VaR / Expected Shortfall and stress-test "
            "losses into a normalized 0-100 indicator."
        ),
        "",
    ]

    return "\n".join(
        lines
    )


def generate_greeks_section(
    portfolio: Portfolio
) -> str:
    """Generate the Greeks exposure section."""

    greeks = portfolio.total_greeks()

    lines = [
        "## Greeks Exposure",
        "",
        "| Greek | Value | Interpretation |",
        "|---|---:|---|",
    ]

    interpretations = {
        "delta": "Directional exposure to the underlying.",
        "gamma": "Convexity and sensitivity of delta to spot moves.",
        "theta": "Time decay under the model assumptions.",
        "vega": "Sensitivity to implied volatility changes.",
        "rho": "Sensitivity to interest-rate changes.",
        "vanna": "Cross-sensitivity between spot and volatility.",
        "volga": "Convexity with respect to volatility.",
    }

    for greek_name, interpretation in interpretations.items():
        lines.append(
            f"| {greek_name.capitalize()} | "
            f"{format_number(greeks[greek_name], 6)} | "
            f"{interpretation} |"
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
    """Generate the stress-test analysis section."""

    lines = [
        "## Stress Test Analysis",
        "",
    ]

    if not scenario_results:
        lines.extend(
            [
                "No stress-test result is available.",
                "",
            ]
        )
        return "\n".join(
            lines
        )

    lines.extend(
        [
            "| Scenario | Spot move | Vol move | P&L | Stressed value |",
            "|---|---:|---:|---:|---:|",
        ]
    )

    for result in scenario_results:
        lines.append(
            "| "
            f"{_localized_scenario_name(result.name, 'en')} | "
            f"{format_percent(result.spot_change_percent)} | "
            f"{format_percent(result.volatility_change_points)} | "
            f"{format_number(result.profit_and_loss)} | "
            f"{format_number(result.stressed_value)} |"
        )

    best_scenario, worst_scenario = _scenario_extremes(
        scenario_results
    )

    lines.extend(
        [
            "",
            (
                f"Best scenario: **{_localized_scenario_name(best_scenario.name, 'en')}** with P&L "
                f"**{format_number(best_scenario.profit_and_loss)}**."
            ),
            (
                f"Worst scenario: **{_localized_scenario_name(worst_scenario.name, 'en')}** with P&L "
                f"**{format_number(worst_scenario.profit_and_loss)}**."
            ),
            "",
        ]
    )

    return "\n".join(
        lines
    )


def generate_var_section(
    var_result: Any,
    parametric_var: float
) -> str:
    """Generate the VaR / Expected Shortfall section."""

    lines = [
        "## VaR / Expected Shortfall Analysis",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Confidence level | {format_percent(var_result.confidence_level)} |",
        f"| Horizon | {var_result.horizon_days} day(s) |",
        f"| Simulations | {var_result.number_of_simulations} |",
        f"| Portfolio value | {format_number(var_result.portfolio_value)} |",
        f"| VaR | {format_number(var_result.var_amount)} |",
        f"| Expected Shortfall | {format_number(var_result.expected_shortfall)} |",
        f"| Worst simulated loss | {format_number(var_result.worst_loss)} |",
        f"| Parametric VaR | {format_number(parametric_var)} |",
        "",
        (
            "VaR estimates a loss threshold at the selected confidence "
            "level. Expected Shortfall focuses on the average loss beyond "
            "that threshold and is therefore more informative in tail events."
        ),
        "",
    ]

    return "\n".join(
        lines
    )


def generate_probabilistic_section(
    probabilistic_result: Any | None
) -> str:
    """Generate the probabilistic risk analysis section."""

    if probabilistic_result is None:
        return ""

    lines = [
        "## Probabilistic Risk Analysis",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Horizon | {probabilistic_result.horizon_days} day(s) |",
        f"| Simulations | {probabilistic_result.number_of_simulations} |",
        f"| Probability of loss | {format_percent(probabilistic_result.probability_of_loss)} |",
        f"| Probability of loss > 5% | {format_percent(probabilistic_result.probability_loss_gt_5)} |",
        f"| Probability of loss > 10% | {format_percent(probabilistic_result.probability_loss_gt_10)} |",
        f"| Probability of loss > 20% | {format_percent(probabilistic_result.probability_loss_gt_20)} |",
        f"| Mean simulated return | {format_percent(probabilistic_result.mean_return)} |",
        f"| Simulated volatility | {format_percent(probabilistic_result.simulated_volatility)} |",
        f"| VaR 95% | {format_percent(probabilistic_result.var_95)} |",
        f"| Expected Shortfall 95% | {format_percent(probabilistic_result.expected_shortfall_95)} |",
        f"| VaR 99% | {format_percent(probabilistic_result.var_99)} |",
        f"| Expected Shortfall 99% | {format_percent(probabilistic_result.expected_shortfall_99)} |",
        f"| Worst simulated return | {format_percent(probabilistic_result.worst_return)} |",
        f"| Best simulated return | {format_percent(probabilistic_result.best_return)} |",
        f"| Main risk driver | {probabilistic_result.main_risk_driver} |",
        "",
        probabilistic_result.interpretation,
        "",
    ]

    if probabilistic_result.top_contributors:
        lines.extend(
            [
                "| Position | Underlying | Contribution | Share |",
                "|---|---|---:|---:|",
            ]
        )
        for contribution in probabilistic_result.top_contributors[:8]:
            lines.append(
                "| "
                f"{contribution.name} | "
                f"{contribution.underlying} | "
                f"{format_number(contribution.downside_contribution)} | "
                f"{format_percent(contribution.contribution_percent)} |"
            )
        lines.append("")

    lines.append(
        "The probabilities above are model outputs, not certain predictions."
    )
    lines.append("")

    return "\n".join(
        lines
    )


def generate_hedge_section(
    hedge_result: Any
) -> str:
    """Generate the delta-hedging recommendation section."""

    if hedge_result.hedge_quantity > 0:
        action = "Buy underlying"

    elif hedge_result.hedge_quantity < 0:
        action = "Sell underlying"

    else:
        action = "No delta action"

    lines = [
        "## Delta Hedging Recommendation",
        "",
        "| Measure | Value |",
        "|---|---:|",
        f"| Current delta | {format_number(hedge_result.current_delta, 6)} |",
        f"| Indicative action | {action} |",
        (
            "| Underlying quantity | "
            f"{format_number(abs(hedge_result.hedge_quantity), 0)} |"
        ),
        f"| Hedge market value | {format_number(hedge_result.hedge_market_value)} |",
        f"| Delta after hedge | {format_number(hedge_result.hedged_delta, 6)} |",
        "",
        hedge_result.explanation,
        "",
        (
            "This is an indicative instantaneous delta hedge. It does not "
            "neutralize gamma, vega, liquidity, transaction costs or model risk."
        ),
        "",
    ]

    return "\n".join(
        lines
    )


def generate_key_risk_drivers_section(
    risk_score_result: Any,
    scenario_results: list[Any],
    var_result: Any
) -> str:
    """Generate the key risk drivers section."""

    lines = [
        "## Key Risk Drivers",
        "",
    ]

    for driver in risk_score_result.main_drivers:
        lines.append(
            f"- {driver}"
        )

    _, worst_scenario = _scenario_extremes(
        scenario_results
    )

    if worst_scenario is not None:
        lines.append(
            f"- Worst stress scenario: {_localized_scenario_name(worst_scenario.name, 'en')} "
            f"({format_number(worst_scenario.profit_and_loss)})"
        )

    lines.append(
        f"- Tail loss indicator: Expected Shortfall "
        f"{format_number(var_result.expected_shortfall)}"
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
    """Generate the quantitative alerts section."""

    lines = [
        "## Quantitative Alerts",
        "",
    ]

    if not alerts:
        lines.extend(
            [
                "No quantitative anomaly was detected.",
                "",
            ]
        )
        return "\n".join(
            lines
        )

    for alert in alerts:
        details = (
            f"- **{alert.severity} - {alert.name}**: {alert.message} "
            f"(current value: {format_number(alert.current_value, 6)}"
        )

        if alert.reference_value is not None:
            details += (
                f", reference: {format_number(alert.reference_value, 6)}"
            )

        if alert.z_score is not None:
            details += (
                f", z-score: {format_number(alert.z_score, 2)}"
            )

        details += ")"
        lines.append(
            details
        )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_llm_section(
    llm_analysis: str | None
) -> str:
    """Generate the LLM commentary section."""

    lines = [
        "## LLM Risk Commentary",
        "",
    ]

    if llm_analysis:
        lines.append(
            llm_analysis
        )

    else:
        lines.append(
            "No LLM commentary was generated for this report."
        )

    lines.append(
        ""
    )

    return "\n".join(
        lines
    )


def generate_limitations_section() -> str:
    """Generate model limitations and assumptions."""

    return "\n".join(
        [
            "## Limitations and Model Assumptions",
            "",
            "- Options are priced with Black-Scholes assumptions.",
            "- Volatility, rates and dividends are simplified inputs.",
            "- Stress tests are scenario based and do not represent forecasts.",
            "- VaR / Expected Shortfall are simplified Monte Carlo estimates.",
            "- Market data quality depends on the selected provider.",
            "- Bloomberg integration is optional and requires a professional setup.",
            "- The report is generated for monitoring and education, not advice.",
            "",
        ]
    )


def generate_recommended_actions_section(
    alerts: list[Any],
    risk_score_result: Any,
    hedge_result: Any
) -> str:
    """Generate recommended monitoring actions."""

    lines = [
        "## Recommended Next Actions",
        "",
        "- Review the ARIA Risk Score and its main drivers before changing positions.",
        "- Monitor delta, gamma and vega against the configured limits.",
        "- Compare the worst stress scenario with the VaR / Expected Shortfall tail metrics.",
        "- Re-run the report after material market moves or portfolio changes.",
        "- Study whether the same market view can be expressed with lower Greek concentration, lower tail loss or tighter downside definition.",
        "- Compare hedge cost against retained upside to improve the risk-adjusted return profile rather than only reducing gross exposure.",
    ]

    if alerts:
        lines.append(
            "- Prioritize quantitative alerts by severity and confirm whether they are driven by Greeks, market moves or history z-scores."
        )

    if hedge_result.hedge_quantity != 0:
        lines.append(
            "- Evaluate the indicative delta hedge, including liquidity, transaction costs and residual gamma / vega exposure."
        )

    if risk_score_result.score >= 60:
        lines.append(
            "- Consider reducing concentrated exposures, using option spreads, or trimming positions that contribute most to downside stress losses."
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
    probabilistic_result: Any | None = None,
    market_snapshot: Any | None = None,
    llm_analysis: str | None = None,
    language: str = "fr"
) -> str:
    """
    Generate a complete Markdown executive risk report.
    """

    language = language.lower()
    if language not in {"fr", "en"}:
        language = "fr"

    report_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    portfolio_value = portfolio.total_market_value()
    greeks = portfolio.total_greeks()
    best_scenario, worst_scenario = _scenario_extremes(
        scenario_results
    )
    drivers = risk_score_result.main_drivers[:4]
    top_alerts = alerts[:3]
    risk_label = _localized_risk_label(
        risk_score_result.label,
        language
    )
    plain_commentary = _plain_language_client_commentary(
        portfolio=portfolio,
        scenario_results=scenario_results,
        var_result=var_result,
        risk_score_result=risk_score_result,
        probabilistic_result=probabilistic_result,
        language=language
    )

    if risk_score_result.score >= 75:
        executive_view = (
            "Le portefeuille présente un risque élevé. La priorité est de réduire "
            "les pertes extrêmes, la concentration et les sensibilités dominantes "
            "avant d'augmenter l'exposition."
        )
    elif risk_score_result.score >= 50:
        executive_view = (
            "Le portefeuille est exploitable mais demande une surveillance active "
            "des stress tests et des Greeks principaux."
        )
    elif risk_score_result.score >= 30:
        executive_view = (
            "Le portefeuille présente un risque intermédiaire. Les couvertures et "
            "la diversification doivent être validées avant renforcement."
        )
    else:
        executive_view = (
            "Le portefeuille ressort comme défensif dans les hypothèses ARIA. "
            "La priorité devient le contrôle du coût de couverture et du potentiel "
            "de rendement conservé."
        )

    action_lines = []
    if hedge_result.hedge_quantity != 0:
        action_lines.append(
            f"- Étudier une couverture delta indicative de {hedge_result.hedge_quantity:,.2f} unités de sous-jacent."
        )
    if worst_scenario is not None:
        action_lines.append(
            "- Réduire ou couvrir les positions qui contribuent au scénario "
            "le plus défavorable : "
            f"{_localized_scenario_name(worst_scenario.name, 'fr')}."
        )
    if drivers:
        action_lines.append(
            "- Traiter en priorité : " + "; ".join(drivers) + "."
        )
    if not action_lines:
        action_lines.append(
            "- Maintenir la discipline de suivi : VaR, stress tests, Greeks et concentration après chaque ajustement."
        )

    table_rows = [
        ("Valeur du portefeuille", format_number(portfolio_value)),
        ("Spot utilisé", format_number(spot)),
        ("Volatilité utilisée", format_percent(volatility)),
        ("Score ARIA", f"{risk_score_result.score}/100 - {risk_label}"),
        ("Nombre d'alertes", str(len(alerts))),
        ("Delta", format_number(greeks["delta"], 4)),
        ("Gamma", format_number(greeks["gamma"], 6)),
        ("Vega", format_number(greeks["vega"], 4)),
        ("VaR", format_number(var_result.var_amount)),
        ("Expected Shortfall", format_number(var_result.expected_shortfall)),
        ("Pire perte simulée", format_number(var_result.worst_loss)),
        ("VaR paramétrique", format_number(parametric_var)),
    ]
    if worst_scenario is not None:
        table_rows.append(
            (
                f"Pire stress - {_localized_scenario_name(worst_scenario.name, 'fr')}",
                format_number(worst_scenario.profit_and_loss),
            )
        )
    if best_scenario is not None:
        table_rows.append(
            (
                f"Meilleur stress - {_localized_scenario_name(best_scenario.name, 'fr')}",
                format_number(best_scenario.profit_and_loss),
            )
        )
    if probabilistic_result is not None:
        table_rows.extend(
            [
                (
                    "Probabilité de perte",
                    format_percent(probabilistic_result.probability_of_loss),
                ),
                (
                    "Probabilité perte > 10%",
                    format_percent(probabilistic_result.probability_loss_gt_10),
                ),
                (
                    "ES 95% probabiliste",
                    format_percent(probabilistic_result.expected_shortfall_95),
                ),
            ]
        )

    if language == "en":
        en_action_lines = []
        if hedge_result.hedge_quantity != 0:
            en_action_lines.append(
                f"- Review an indicative delta hedge of {hedge_result.hedge_quantity:,.2f} units of the underlying."
            )
        if worst_scenario is not None:
            en_action_lines.append(
                "- Reduce or hedge positions contributing to the worst scenario: "
                + _localized_scenario_name(worst_scenario.name, "en")
                + "."
            )
        if drivers:
            en_action_lines.append(
                "- Priority drivers: " + "; ".join(drivers) + "."
            )
        if not en_action_lines:
            en_action_lines.append(
                "- Keep monitoring VaR, stress tests, Greeks and concentration after each adjustment."
            )

        en_table_rows = [
            ("Portfolio value", format_number(portfolio_value)),
            ("Spot used", format_number(spot)),
            ("Volatility used", format_percent(volatility)),
            ("ARIA Score", f"{risk_score_result.score}/100 - {risk_label}"),
            ("Number of alerts", str(len(alerts))),
            ("Delta", format_number(greeks["delta"], 4)),
            ("Gamma", format_number(greeks["gamma"], 6)),
            ("Vega", format_number(greeks["vega"], 4)),
            ("VaR", format_number(var_result.var_amount)),
            ("Expected Shortfall", format_number(var_result.expected_shortfall)),
            ("Worst simulated loss", format_number(var_result.worst_loss)),
            ("Parametric VaR", format_number(parametric_var)),
        ]
        if worst_scenario is not None:
            en_table_rows.append(
                (
                    "Worst stress - "
                    + _localized_scenario_name(worst_scenario.name, "en"),
                    format_number(worst_scenario.profit_and_loss),
                )
            )
        if best_scenario is not None:
            en_table_rows.append(
                (
                    "Best stress - "
                    + _localized_scenario_name(best_scenario.name, "en"),
                    format_number(best_scenario.profit_and_loss),
                )
            )
        if probabilistic_result is not None:
            en_table_rows.extend(
                [
                    (
                        "Probability of loss",
                        format_percent(probabilistic_result.probability_of_loss),
                    ),
                    (
                        "Probability loss > 10%",
                        format_percent(probabilistic_result.probability_loss_gt_10),
                    ),
                    (
                        "Probabilistic ES 95%",
                        format_percent(probabilistic_result.expected_shortfall_95),
                    ),
                ]
            )

        en_executive_view = (
            "The portfolio shows high risk. Priority should be given to reducing extreme losses, concentration and dominant sensitivities before adding exposure."
            if risk_score_result.score >= 75
            else (
                "The portfolio is usable, but requires active monitoring of stress tests and main Greeks."
                if risk_score_result.score >= 50
                else (
                    "The portfolio has intermediate risk. Hedges and diversification should be reviewed before increasing exposure."
                    if risk_score_result.score >= 30
                    else "The portfolio appears defensive under ARIA assumptions. The key point is to monitor hedge cost and retained return potential."
                )
            )
        )
        en_worst_line = (
            f"- Worst stress: **{_localized_scenario_name(worst_scenario.name, 'en')}** for **{format_number(worst_scenario.profit_and_loss)}**."
            if worst_scenario is not None
            else "- Worst stress: not available."
        )
        en_alert_lines = (
            [
                f"- Priority alert: {alert.name} - {alert.message}"
                for alert in top_alerts
            ]
            if top_alerts
            else ["- No priority quantitative alert."]
        )
        en_lines = [
            "# ARIA - Executive Risk Report",
            "",
            f"Prepared by: **{AUTHOR_NAME}**",
            "",
            f"Generated on: **{report_date}**",
            "",
            "## 1. Plain-language client explanation",
            "",
            plain_commentary,
            "",
            "## 2. Executive view",
            "",
            en_executive_view,
            "",
            "## 3. Risk diagnosis",
            "",
            f"- ARIA Score: **{risk_score_result.score}/100 - {risk_label}**.",
            f"- VaR: **{format_number(var_result.var_amount)}** ; Expected Shortfall: **{format_number(var_result.expected_shortfall)}**.",
            en_worst_line,
            "",
            "## 4. Key points",
            "",
            *[f"- {driver}" for driver in drivers],
            *en_alert_lines,
            "",
            "## 5. Actions to review",
            "",
            *en_action_lines,
            "",
            (
                llm_analysis
                if llm_analysis
                else "LLM commentary disabled. The recommendations above come from ARIA quantitative metrics."
            ),
            "",
            "## 6. Disclaimer",
            "",
            (
                "These elements support risk-management decisions. They are not performance certainty or personalized financial advice. "
                "Any action must be reviewed against market assumptions, liquidity and real constraints."
            ),
            "",
            "## Appendix - key figures",
            "",
            "| Metric | Value |",
            "|---|---:|",
            *[f"| {name} | {value} |" for name, value in en_table_rows],
            "",
        ]

        return "\n".join(en_lines)

    lines = [
        "# ARIA - Rapport exécutif de risque",
        "",
        f"Préparé par : **{AUTHOR_NAME}**",
        "",
        f"Généré le : **{report_date}**",
        "",
        "## 1. Explication simple pour le client",
        "",
        plain_commentary,
        "",
        "## 2. Vue exécutive",
        "",
        executive_view,
        "",
        "## 3. Diagnostic de risque",
        "",
        f"- Score ARIA : **{risk_score_result.score}/100 - {risk_label}**.",
        f"- VaR : **{format_number(var_result.var_amount)}** ; Expected Shortfall : **{format_number(var_result.expected_shortfall)}**.",
        (
            f"- Pire stress : **{_localized_scenario_name(worst_scenario.name, 'fr')}** pour **{format_number(worst_scenario.profit_and_loss)}**."
            if worst_scenario is not None
            else "- Pire stress : non disponible."
        ),
        "",
        "## 4. Points clés",
        "",
        *[f"- {driver}" for driver in drivers],
        *(
            [f"- Alerte prioritaire : {alert.name} - {alert.message}" for alert in top_alerts]
            if top_alerts
            else ["- Aucune alerte quantitative prioritaire."]
        ),
        "",
        "## 5. Recommandations à étudier",
        "",
        *action_lines,
        "",
        (
            llm_analysis
            if llm_analysis
            else "Commentaire LLM non activé. Les recommandations ci-dessus proviennent des métriques ARIA."
        ),
        "",
        "## 6. Avertissement",
        "",
        (
            "Ces éléments sont une aide à la décision de gestion du risque. "
            "Ils ne constituent pas une certitude de performance ni un conseil "
            "financier personnalisé. Toute action doit être vérifiée avec les "
            "hypothèses de marché, la liquidité et les contraintes réelles."
        ),
        "",
        "## Annexe - chiffres significatifs",
        "",
        "| Indicateur | Valeur |",
        "|---|---:|",
        *[f"| {name} | {value} |" for name, value in table_rows],
        "",
    ]

    return "\n".join(
        lines
    )


def generate_executive_risk_report(
    portfolio: Portfolio,
    spot: float,
    volatility: float,
    alerts: list[Any],
    scenario_results: list[Any],
    var_result: Any,
    parametric_var: float,
    hedge_result: Any,
    risk_score_result: Any,
    probabilistic_result: Any | None = None,
    market_snapshot: Any | None = None,
    llm_analysis: str | None = None,
    language: str = "fr"
) -> str:
    """Explicit alias for the executive report format."""

    return generate_risk_report(
        portfolio=portfolio,
        spot=spot,
        volatility=volatility,
        alerts=alerts,
        scenario_results=scenario_results,
        var_result=var_result,
        parametric_var=parametric_var,
        probabilistic_result=probabilistic_result,
        hedge_result=hedge_result,
        risk_score_result=risk_score_result,
        market_snapshot=market_snapshot,
        llm_analysis=llm_analysis,
        language=language
    )


def _clean_markdown_for_pdf(
    line: str
) -> str:
    """Convert a simple Markdown line to plain text for PDF rendering."""

    cleaned = line.replace(
        "**",
        ""
    )
    cleaned = cleaned.replace(
        "|",
        "  "
    )
    cleaned = cleaned.replace(
        "---",
        ""
    )
    cleaned = cleaned.replace(
        "# ",
        ""
    )
    cleaned = cleaned.replace(
        "## ",
        ""
    )
    cleaned = cleaned.replace(
        "- ",
        "* "
    )

    return cleaned.strip()


PDF_ACCENT = colors.HexColor(
    "#10B981"
)
PDF_DARK = colors.HexColor(
    "#111827"
)
PDF_MUTED = colors.HexColor(
    "#6B7280"
)
PDF_LIGHT = colors.HexColor(
    "#F3F7F6"
)
PDF_BORDER = colors.HexColor(
    "#D7E2DF"
)


def _as_text(
    value: Any,
    default: str = "N/A"
) -> str:
    """Convert a report value to a display string."""

    if value is None:
        return default

    return str(
        value
    )


def _pdf_styles() -> dict[str, ParagraphStyle]:
    """Return professional PDF styles."""

    base_styles = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=32,
            textColor=PDF_DARK,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=PDF_MUTED,
            alignment=TA_LEFT,
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=PDF_DARK,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "subsection": ParagraphStyle(
            "Subsection",
            parent=base_styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=PDF_DARK,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1F2937"),
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=PDF_MUTED,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base_styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=PDF_DARK,
            backColor=PDF_LIGHT,
            borderColor=PDF_BORDER,
            borderWidth=0.7,
            borderPadding=8,
            spaceAfter=10,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=PDF_MUTED,
            alignment=TA_CENTER,
        ),
    }

    return styles


def _p(
    text: str,
    style: ParagraphStyle
) -> Paragraph:
    """Create an escaped ReportLab paragraph."""

    return Paragraph(
        escape(
            text
        ).replace(
            "\n",
            "<br/>"
        ),
        style
    )


def _section(
    story: list[Any],
    title: str,
    styles: dict[str, ParagraphStyle]
) -> None:
    """Append a section title to a story."""

    story.append(
        Paragraph(
            escape(
                title
            ),
            styles["section"]
        )
    )


def _table(
    rows: list[list[Any]],
    widths: list[float] | None = None,
    header: bool = True
) -> Table:
    """Create a consistent PDF table."""

    table_data = [
        [
            Paragraph(
                escape(
                    _as_text(
                        cell
                    )
                ),
                _pdf_styles()["body"]
            )
            for cell in row
        ]
        for row in rows
    ]

    table = Table(
        table_data,
        colWidths=widths,
        hAlign="LEFT",
        repeatRows=1 if header else 0,
    )

    style_commands = [
        (
            "GRID",
            (
                0,
                0
            ),
            (
                -1,
                -1
            ),
            0.35,
            PDF_BORDER,
        ),
        (
            "VALIGN",
            (
                0,
                0
            ),
            (
                -1,
                -1
            ),
            "TOP",
        ),
        (
            "LEFTPADDING",
            (
                0,
                0
            ),
            (
                -1,
                -1
            ),
            6,
        ),
        (
            "RIGHTPADDING",
            (
                0,
                0
            ),
            (
                -1,
                -1
            ),
            6,
        ),
        (
            "TOPPADDING",
            (
                0,
                0
            ),
            (
                -1,
                -1
            ),
            5,
        ),
        (
            "BOTTOMPADDING",
            (
                0,
                0
            ),
            (
                -1,
                -1
            ),
            5,
        ),
    ]

    if header:
        style_commands.extend(
            [
                (
                    "BACKGROUND",
                    (
                        0,
                        0
                    ),
                    (
                        -1,
                        0
                    ),
                    colors.HexColor(
                        "#E8F7F2"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (
                        0,
                        0
                    ),
                    (
                        -1,
                        0
                    ),
                    PDF_DARK,
                ),
            ]
        )

    table.setStyle(
        TableStyle(
            style_commands
        )
    )

    return table


def _add_paragraph_block(
    story: list[Any],
    text: str | None,
    styles: dict[str, ParagraphStyle]
) -> None:
    """Append a multiline block as readable paragraphs."""

    if not text:
        return

    for block in text.split(
        "\n"
    ):
        cleaned = _clean_markdown_for_pdf(
            block
        )

        if not cleaned:
            story.append(
                Spacer(
                    1,
                    4
                )
            )
            continue

        story.append(
            _p(
                cleaned,
                styles["body"]
            )
        )


def _hedge_action_text(
    hedge_result: Any,
    language: str
) -> str:
    """Return a concrete but cautious delta hedge action."""

    quantity = abs(
        hedge_result.hedge_quantity
    )

    if hedge_result.hedge_quantity > 0:
        verb = "Acheter" if language == "fr" else "Buy"

    elif hedge_result.hedge_quantity < 0:
        verb = "Vendre" if language == "fr" else "Sell"

    else:
        return (
            "Aucune couverture delta immediate n'est suggeree par le modele."
            if language == "fr"
            else "No immediate delta hedge is suggested by the model."
        )

    if language == "fr":
        return (
            f"{verb} environ {format_number(quantity, 0)} unites du sous-jacent "
            "pour rapprocher le delta de zero selon le modele ARIA."
        )

    return (
        f"{verb} about {format_number(quantity, 0)} units of the underlying "
        "to move model delta closer to zero."
    )


def _build_action_rows(
    alerts: list[Any],
    scenario_results: list[Any],
    var_result: Any,
    hedge_result: Any,
    risk_score_result: Any,
    language: str
) -> list[list[str]]:
    """Build concrete risk-management actions for the PDF."""

    _, worst_scenario = _scenario_extremes(
        scenario_results
    )

    rows = [
        [
            "Priorite" if language == "fr" else "Priority",
            "Action indicative" if language == "fr" else "Indicative action",
            "Objectif" if language == "fr" else "Objective",
        ],
        [
            "1",
            _hedge_action_text(
                hedge_result,
                language
            ),
            (
                "Reduire l'exposition directionnelle immediate tout en conservant une partie du potentiel optionnel."
                if language == "fr"
                else "Reduce immediate directional exposure while retaining part of the optionality."
            ),
        ],
    ]

    if risk_score_result.score >= 60:
        rows.append(
            [
                "2",
                (
                    "Reduire ou transformer les positions qui contribuent au score de risque: taille plus faible, spread optionnel, ou maturites moins concentrees."
                    if language == "fr"
                    else "Reduce or reshape positions driving the risk score: smaller size, option spread, or less concentrated maturities."
                ),
                (
                    "Diminuer le risque de queue sans supprimer toute l'exposition au rendement."
                    if language == "fr"
                    else "Lower tail risk without eliminating all return exposure."
                ),
            ]
        )

    if worst_scenario is not None:
        worst_name = _localized_scenario_name(
            worst_scenario.name,
            language
        )
        rows.append(
            [
                "3",
                (
                    f"Tester une reduction des lignes responsables du scenario le plus defavorable: {worst_name}, P&L {format_number(worst_scenario.profit_and_loss)}."
                    if language == "fr"
                    else f"Test reducing lines responsible for the worst scenario: {worst_name}, P&L {format_number(worst_scenario.profit_and_loss)}."
                ),
                (
                    "Ramener la perte de stress dans une zone acceptable avant d'augmenter le risque."
                    if language == "fr"
                    else "Bring stress loss into an acceptable zone before adding risk."
                ),
            ]
        )

    rows.append(
        [
            "4",
            (
                f"Comparer la VaR {format_number(var_result.var_amount)} et l'Expected Shortfall {format_number(var_result.expected_shortfall)} apres chaque ajustement."
                if language == "fr"
                else f"Compare VaR {format_number(var_result.var_amount)} and Expected Shortfall {format_number(var_result.expected_shortfall)} after each adjustment."
            ),
            (
                "Optimiser le rendement ajuste du risque, pas seulement reduire l'exposition brute."
                if language == "fr"
                else "Optimize risk-adjusted return, not only gross exposure."
            ),
        ]
    )

    if alerts:
        rows.append(
            [
                "5",
                (
                    "Traiter d'abord les alertes critiques et elevees, puis relancer le rapport apres modification."
                    if language == "fr"
                    else "Address critical and high alerts first, then rerun the report after changes."
                ),
                (
                    "Verifier que les actions reduisent vraiment les facteurs de risque signales."
                    if language == "fr"
                    else "Check that the actions really reduce the flagged risk drivers."
                ),
            ]
        )

    return rows


def _key_metric_rows(
    portfolio: Portfolio,
    spot: float,
    volatility: float,
    scenario_results: list[Any],
    var_result: Any,
    parametric_var: float,
    hedge_result: Any,
    risk_score_result: Any,
    probabilistic_result: Any | None = None,
    language: str = "fr"
) -> list[list[str]]:
    """Build appendix key metrics."""

    greeks = portfolio.total_greeks()
    best_scenario, worst_scenario = _scenario_extremes(
        scenario_results
    )
    rows = [
        [
            "Indicateur" if language == "fr" else "Metric",
            "Valeur" if language == "fr" else "Value",
        ],
        [
            "Valeur du portefeuille" if language == "fr" else "Portfolio value",
            format_number(
                portfolio.total_market_value()
            ),
        ],
        [
            "Spot",
            format_number(
                spot
            ),
        ],
        [
            "Volatilite" if language == "fr" else "Volatility",
            format_percent(
                volatility
            ),
        ],
        [
            "Risk Score",
            f"{risk_score_result.score}/100 - {_localized_risk_label(risk_score_result.label, language)}",
        ],
        [
            "Delta",
            format_number(
                greeks["delta"],
                6
            ),
        ],
        [
            "Gamma",
            format_number(
                greeks["gamma"],
                6
            ),
        ],
        [
            "Vega",
            format_number(
                greeks["vega"],
                6
            ),
        ],
        [
            "Theta",
            format_number(
                greeks["theta"],
                6
            ),
        ],
        [
            "VaR",
            format_number(
                var_result.var_amount
            ),
        ],
        [
            "Expected Shortfall",
            format_number(
                var_result.expected_shortfall
            ),
        ],
        [
            "VaR parametrique" if language == "fr" else "Parametric VaR",
            format_number(
                parametric_var
            ),
        ],
        [
            "Quantite hedge" if language == "fr" else "Hedge quantity",
            format_number(
                hedge_result.hedge_quantity,
                0
            ),
        ],
    ]

    if worst_scenario is not None:
        rows.append(
            [
                "Pire stress" if language == "fr" else "Worst stress",
                (
                    f"{_localized_scenario_name(worst_scenario.name, language)}: "
                    f"{format_number(worst_scenario.profit_and_loss)}"
                ),
            ]
        )

    if probabilistic_result is not None:
        rows.extend(
            [
                [
                    "Probabilite de perte" if language == "fr" else "Probability of loss",
                    format_percent(
                        probabilistic_result.probability_of_loss
                    ),
                ],
                [
                    "Perte > 10%" if language == "fr" else "Loss > 10%",
                    format_percent(
                        probabilistic_result.probability_loss_gt_10
                    ),
                ],
                [
                    "Moteur probabiliste" if language == "fr" else "Probabilistic driver",
                    probabilistic_result.main_risk_driver,
                ],
            ]
        )

    if best_scenario is not None:
        rows.append(
            [
                "Meilleur stress" if language == "fr" else "Best stress",
                (
                    f"{_localized_scenario_name(best_scenario.name, language)}: "
                    f"{format_number(best_scenario.profit_and_loss)}"
                ),
            ]
        )

    return rows


def _market_rows(
    market_snapshot: Any | None,
    language: str
) -> list[list[str]]:
    """Build market context rows."""

    rows = [
        [
            "Donnee" if language == "fr" else "Data",
            "Valeur" if language == "fr" else "Value",
        ]
    ]

    if market_snapshot is None:
        rows.append(
            [
                "Source",
                "Manuelle / non disponible" if language == "fr" else "Manual / not available",
            ]
        )
        return rows

    rows.extend(
        [
            [
                "Source",
                _as_text(
                    getattr(
                        market_snapshot,
                        "source",
                        None
                    )
                ),
            ],
            [
                "Ticker",
                _as_text(
                    getattr(
                        market_snapshot,
                        "ticker",
                        None
                    )
                ),
            ],
            [
                "Dernier prix" if language == "fr" else "Last price",
                format_number(
                    market_snapshot.last_price
                ),
            ],
            [
                "Rendement journalier" if language == "fr" else "Daily return",
                format_percent(
                    market_snapshot.daily_return
                ),
            ],
            [
                "Volatilite annualisee" if language == "fr" else "Annualized volatility",
                format_percent(
                    market_snapshot.annualized_volatility
                ),
            ],
        ]
    )

    return rows


def _build_executive_decision_rows(
    scenario_results: list[Any],
    var_result: Any,
    risk_score_result: Any,
    probabilistic_result: Any | None,
    language: str
) -> list[list[str]]:
    """Build the opening decision table for the downloadable PDF."""

    _, worst_scenario = _scenario_extremes(
        scenario_results
    )

    if risk_score_result.score >= 75:
        verdict = (
            "Risque eleve: reduire ou couvrir avant d'ajouter du risque."
            if language == "fr"
            else "High risk: reduce or hedge before adding risk."
        )
    elif risk_score_result.score >= 50:
        verdict = (
            "Risque significatif: surveiller les stress et les sensibilites."
            if language == "fr"
            else "Material risk: monitor stress losses and sensitivities."
        )
    elif risk_score_result.score >= 30:
        verdict = (
            "Risque intermediaire: portefeuille exploitable avec discipline de suivi."
            if language == "fr"
            else "Intermediate risk: usable portfolio with disciplined monitoring."
        )
    else:
        verdict = (
            "Risque contenu: verifier surtout le cout de couverture et le rendement conserve."
            if language == "fr"
            else "Contained risk: mainly review hedging cost and retained return."
        )

    rows = [
        [
            "Point" if language == "fr" else "Item",
            "Lecture" if language == "fr" else "Read",
            "Action proposee" if language == "fr" else "Suggested action",
        ],
        [
            "Score ARIA",
            f"{risk_score_result.score}/100 - {_localized_risk_label(risk_score_result.label, language)}",
            verdict,
        ],
        [
            "VaR / ES",
            (
                f"VaR {format_number(var_result.var_amount)} ; "
                f"ES {format_number(var_result.expected_shortfall)}"
            ),
            (
                "Comparer au budget de perte et recalculer apres chaque ajustement."
                if language == "fr"
                else "Compare with the loss budget and recompute after each adjustment."
            ),
        ],
    ]

    if worst_scenario is not None:
        rows.append(
            [
                "Pire stress" if language == "fr" else "Worst stress",
                (
                    f"{_localized_scenario_name(worst_scenario.name, language)}: "
                    f"{format_number(worst_scenario.profit_and_loss)}"
                ),
                (
                    "Identifier les lignes contributrices puis tester reduction, spread ou couverture."
                    if language == "fr"
                    else "Identify contributing lines, then test trimming, spreading or hedging."
                ),
            ]
        )

    if probabilistic_result is not None:
        rows.append(
            [
                "Monte Carlo",
                (
                    f"Perte {format_percent(probabilistic_result.probability_of_loss)} ; "
                    f"perte >10% {format_percent(probabilistic_result.probability_loss_gt_10)}"
                ),
                (
                    "Prioriser le controle des pertes de queue et du moteur probabiliste principal."
                    if language == "fr"
                    else "Prioritize tail-loss control and the main probabilistic driver."
                ),
            ]
        )

    return rows


def _portfolio_position_rows(
    portfolio: Portfolio,
    language: str
) -> list[list[str]]:
    """Build a compact PDF snapshot of the largest positions."""

    gross_value = sum(
        abs(
            position.market_value()
        )
        for position in portfolio.positions
    )
    gross_value = max(
        gross_value,
        1.0
    )

    rows = [
        [
            "Position",
            "Sous-jacent" if language == "fr" else "Underlying",
            "Type",
            "Quantite" if language == "fr" else "Quantity",
            "Valeur" if language == "fr" else "Value",
            "Poids brut" if language == "fr" else "Gross weight",
        ]
    ]

    sorted_positions = sorted(
        portfolio.positions,
        key=lambda position: abs(
            position.market_value()
        ),
        reverse=True,
    )

    for position in sorted_positions[:8]:
        raw_position_type = position.__class__.__name__.replace(
            "Position",
            ""
        )
        position_type = {
            "Stock": "Action / ETF" if language == "fr" else "Equity / ETF",
            "Option": "Option",
        }.get(
            raw_position_type,
            raw_position_type,
        )
        rows.append(
            [
                position.name,
                position.underlying,
                position_type,
                format_number(
                    position.quantity,
                    2
                ),
                format_number(
                    position.market_value()
                ),
                format_percent(
                    abs(
                        position.market_value()
                    ) / gross_value
                ),
            ]
        )

    return rows


def _draw_pdf_page(
    canvas,
    doc,
    title: str,
    author_name: str
) -> None:
    """Draw repeated professional header/footer."""

    width, height = A4
    canvas.saveState()
    canvas.setFillColor(
        PDF_ACCENT
    )
    canvas.rect(
        0,
        height - 0.35 * cm,
        width,
        0.35 * cm,
        fill=1,
        stroke=0,
    )
    canvas.setFillColor(
        PDF_DARK
    )
    canvas.setFont(
        "Helvetica-Bold",
        8.5
    )
    canvas.drawString(
        doc.leftMargin,
        height - 0.9 * cm,
        title
    )
    canvas.setFillColor(
        PDF_MUTED
    )
    canvas.setFont(
        "Helvetica",
        7.5
    )
    canvas.drawRightString(
        width - doc.rightMargin,
        height - 0.9 * cm,
        f"Developed by {author_name}"
    )
    canvas.drawRightString(
        width - doc.rightMargin,
        0.55 * cm,
        f"Page {doc.page}"
    )
    canvas.restoreState()


def generate_professional_pdf_report(
    portfolio: Portfolio,
    spot: float,
    volatility: float,
    alerts: list[Any],
    scenario_results: list[Any],
    var_result: Any,
    parametric_var: float,
    hedge_result: Any,
    risk_score_result: Any,
    probabilistic_result: Any | None = None,
    market_snapshot: Any | None = None,
    llm_analysis: str | None = None,
    language: str = "fr",
    author_name: str = AUTHOR_NAME
) -> bytes:
    """Generate a polished FR/EN PDF risk report."""

    language = language.lower()
    if language not in {
        "fr",
        "en"
    }:
        raise ValueError(
            "language must be 'fr' or 'en'"
        )

    styles = _pdf_styles()
    buffer = BytesIO()
    doc_title = (
        "ARIA - Note professionnelle de risque"
        if language == "fr"
        else "ARIA Professional Risk Report"
    )
    report_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.2 * cm,
        title=doc_title,
        author=author_name,
    )

    story: list[Any] = []

    story.append(
        Spacer(
            1,
            1.0 * cm
        )
    )
    story.append(
        Paragraph(
            escape(
                doc_title
            ),
            styles["cover_title"]
        )
    )
    story.append(
        _p(
            (
                f"Prepare par {author_name} | Genere le {report_date}"
                if language == "fr"
                else f"Prepared by {author_name} | Generated on {report_date}"
            ),
            styles["cover_subtitle"]
        )
    )
    story.append(
        _table(
            _key_metric_rows(
                portfolio=portfolio,
                spot=spot,
                volatility=volatility,
                scenario_results=scenario_results,
                var_result=var_result,
                parametric_var=parametric_var,
                hedge_result=hedge_result,
                risk_score_result=risk_score_result,
                probabilistic_result=probabilistic_result,
                language=language
            )[:8],
            widths=[
                7.2 * cm,
                8.8 * cm
            ],
        )
    )
    story.append(
        Spacer(
            1,
            12
        )
    )
    story.append(
        _p(
            (
                "Document de synthese pour entretien et revue de risque: diagnostic, stress tests, VaR, Monte Carlo, "
                "Greeks, actions concretes et annexe des chiffres a retenir. Les actions indiquees sont des pistes "
                "de risk management a valider, pas une garantie de rendement."
                if language == "fr"
                else "Interview and risk-review memo: diagnosis, stress tests, VaR, Monte Carlo, Greeks, concrete "
                "actions and appendix of key figures. The listed actions are risk-management ideas to validate, "
                "not a guarantee of performance."
            ),
            styles["callout"]
        )
    )

    _section(
        story,
        "Explication simple pour le client"
        if language == "fr"
        else "Plain-Language Client Explanation",
        styles
    )
    story.append(
        _p(
            _plain_language_client_commentary(
                portfolio=portfolio,
                scenario_results=scenario_results,
                var_result=var_result,
                risk_score_result=risk_score_result,
                probabilistic_result=probabilistic_result,
                language=language
            ),
            styles["callout"]
        )
    )

    _section(
        story,
        "Synthese decisionnelle" if language == "fr" else "Decision Summary",
        styles
    )
    story.append(
        _table(
            _build_executive_decision_rows(
                scenario_results=scenario_results,
                var_result=var_result,
                risk_score_result=risk_score_result,
                probabilistic_result=probabilistic_result,
                language=language
            ),
            widths=[
                3.0 * cm,
                5.6 * cm,
                7.4 * cm
            ],
        )
    )
    story.append(
        Spacer(
            1,
            8
        )
    )
    story.append(
        _p(
            (
                "Lecture ARIA: l'objectif n'est pas de supprimer tout risque, mais de reduire les pertes extremes, "
                "controler les expositions dominantes et conserver un rendement ajuste du risque defendable."
                if language == "fr"
                else "ARIA read: the goal is not to remove all risk, but to reduce extreme losses, control dominant "
                "exposures and retain a defensible risk-adjusted return."
            ),
            styles["body"]
        )
    )

    _section(
        story,
        "Commentaire LLM optionnel" if language == "fr" else "Optional LLM Commentary",
        styles
    )

    if llm_analysis:
        _add_paragraph_block(
            story,
            llm_analysis,
            styles
        )

    else:
        story.append(
            _p(
                (
                    "Commentaire LLM non activé. La lecture ci-dessus reste générée par ARIA à partir des métriques quantitatives."
                    if language == "fr"
                    else "LLM commentary is disabled. The client explanation above is generated by ARIA from quantitative metrics."
                ),
                styles["body"]
            )
        )

    _section(
        story,
        "Plan d'action: diminuer le risque et optimiser le rendement ajuste du risque"
        if language == "fr"
        else "Action Plan: Reduce Risk and Optimize Risk-Adjusted Return",
        styles
    )
    story.append(
        _table(
            _build_action_rows(
                alerts=alerts,
                scenario_results=scenario_results,
                var_result=var_result,
                hedge_result=hedge_result,
                risk_score_result=risk_score_result,
                language=language
            ),
            widths=[
                1.6 * cm,
                8.6 * cm,
                5.8 * cm
            ],
        )
    )
    story.append(
        PageBreak()
    )

    _section(
        story,
        "Contexte de marche, score et portefeuille" if language == "fr" else "Market Context, Score and Portfolio",
        styles
    )
    story.append(
        _table(
            _market_rows(
                market_snapshot,
                language
            ),
            widths=[
                7.2 * cm,
                8.8 * cm
            ],
        )
    )
    story.append(
        Spacer(
            1,
            8
        )
    )
    story.append(
        _p(
            (
                f"Risk Score ARIA: {risk_score_result.score}/100 - "
                f"{_localized_risk_label(risk_score_result.label, language)}. "
                f"{_localized_risk_explanation(risk_score_result.score, risk_score_result.explanation, language)}"
            ),
            styles["body"]
        )
    )
    story.append(
        Spacer(
            1,
            8
        )
    )
    story.append(
        _table(
            _portfolio_position_rows(
                portfolio,
                language
            ),
            widths=[
                4.0 * cm,
                3.0 * cm,
                2.3 * cm,
                2.2 * cm,
                2.4 * cm,
                2.1 * cm
            ],
        )
    )

    _section(
        story,
        "Stress tests, VaR et Expected Shortfall" if language == "fr" else "Stress Tests, VaR and Expected Shortfall",
        styles
    )
    stress_rows = [
        [
            "Scenario" if language == "fr" else "Scenario",
            "Variation spot" if language == "fr" else "Spot move",
            "Variation vol" if language == "fr" else "Vol move",
            "P&L",
        ]
    ]
    for result in scenario_results:
        stress_rows.append(
            [
                _localized_scenario_name(
                    result.name,
                    language
                ),
                format_percent(
                    result.spot_change_percent
                ),
                format_percent(
                    result.volatility_change_points
                ),
                format_number(
                    result.profit_and_loss
                ),
            ]
        )
    story.append(
        _table(
            stress_rows,
            widths=[
                5.8 * cm,
                3.2 * cm,
                3.2 * cm,
                3.8 * cm
            ],
        )
    )
    story.append(
        Spacer(
            1,
            8
        )
    )
    story.append(
        _table(
            [
                [
                    "Mesure" if language == "fr" else "Measure",
                    "Valeur" if language == "fr" else "Value",
                ],
                [
                    "VaR",
                    format_number(
                        var_result.var_amount
                    ),
                ],
                [
                    "Expected Shortfall",
                    format_number(
                        var_result.expected_shortfall
                    ),
                ],
                [
                    "Pire perte simulee" if language == "fr" else "Worst simulated loss",
                    format_number(
                        var_result.worst_loss
                    ),
                ],
                [
                    "VaR parametrique" if language == "fr" else "Parametric VaR",
                    format_number(
                        parametric_var
                    ),
                ],
            ],
            widths=[
                7.2 * cm,
                8.8 * cm
            ],
        )
    )

    if probabilistic_result is not None:
        _section(
            story,
            "Analyse probabiliste Monte Carlo" if language == "fr" else "Monte Carlo Probabilistic Analysis",
            styles
        )
        story.append(
            _table(
                [
                    [
                        "Mesure" if language == "fr" else "Measure",
                        "Valeur" if language == "fr" else "Value",
                    ],
                    [
                        "Probabilite de perte" if language == "fr" else "Probability of loss",
                        format_percent(
                            probabilistic_result.probability_of_loss
                        ),
                    ],
                    [
                        "Probabilite perte > 10%" if language == "fr" else "Probability loss > 10%",
                        format_percent(
                            probabilistic_result.probability_loss_gt_10
                        ),
                    ],
                    [
                        "VaR 95%",
                        format_percent(
                            probabilistic_result.var_95
                        ),
                    ],
                    [
                        "Expected Shortfall 95%",
                        format_percent(
                            probabilistic_result.expected_shortfall_95
                        ),
                    ],
                    [
                        "Rendement moyen simule" if language == "fr" else "Mean simulated return",
                        format_percent(
                            probabilistic_result.mean_return
                        ),
                    ],
                    [
                        "Volatilite simulee" if language == "fr" else "Simulated volatility",
                        format_percent(
                            probabilistic_result.simulated_volatility
                        ),
                    ],
                    [
                        "Moteur principal" if language == "fr" else "Main risk driver",
                        probabilistic_result.main_risk_driver,
                    ],
                ],
                widths=[
                    7.2 * cm,
                    8.8 * cm
                ],
            )
        )
        story.append(
            Spacer(
                1,
                8
            )
        )
        story.append(
            _p(
                _localized_probabilistic_interpretation(
                    probabilistic_result,
                    language
                ),
                styles["callout"]
            )
        )

        if probabilistic_result.top_contributors:
            contribution_rows = [
                [
                    "Position",
                    "Sous-jacent" if language == "fr" else "Underlying",
                    "Part" if language == "fr" else "Share",
                ]
            ]
            for contribution in probabilistic_result.top_contributors[:6]:
                contribution_rows.append(
                    [
                        contribution.name,
                        contribution.underlying,
                        format_percent(
                            contribution.contribution_percent
                        ),
                    ]
                )
            story.append(
                _table(
                    contribution_rows,
                    widths=[
                        7.2 * cm,
                        4.0 * cm,
                        4.8 * cm
                    ],
                )
            )

    _section(
        story,
        "Greeks et couverture" if language == "fr" else "Greeks and Hedging",
        styles
    )
    greeks = portfolio.total_greeks()
    story.append(
        _table(
            [
                [
                    "Greek",
                    "Valeur" if language == "fr" else "Value",
                ],
                [
                    "Delta",
                    format_number(
                        greeks["delta"],
                        6
                    ),
                ],
                [
                    "Gamma",
                    format_number(
                        greeks["gamma"],
                        6
                    ),
                ],
                [
                    "Vega",
                    format_number(
                        greeks["vega"],
                        6
                    ),
                ],
                [
                    "Theta",
                    format_number(
                        greeks["theta"],
                        6
                    ),
                ],
                [
                    "Rho",
                    format_number(
                        greeks["rho"],
                        6
                    ),
                ],
            ],
            widths=[
                7.2 * cm,
                8.8 * cm
            ],
        )
    )
    story.append(
        Spacer(
            1,
            8
        )
    )
    story.append(
        _p(
            _hedge_action_text(
                hedge_result,
                language
            ),
            styles["callout"]
        )
    )

    _section(
        story,
        "Limites et avertissement" if language == "fr" else "Limits and Disclaimer",
        styles
    )
    story.append(
        _p(
            (
                "Les resultats dependent du modele Black-Scholes, des hypotheses de volatilite, des scenarios, de la liquidite et des couts de transaction. "
                "Les actions proposees sont des pistes d'analyse et de gestion du risque. Elles ne constituent pas une recommandation financiere personnalisee, "
                "ne sont pas une certitude de performance et doivent etre verifiees avant toute decision reelle."
                if language == "fr"
                else "Results depend on Black-Scholes assumptions, volatility inputs, scenarios, liquidity and transaction costs. "
                "The proposed actions are risk-analysis and risk-management ideas. They are not personalized financial advice, "
                "are not a certainty of performance, and must be validated before any real decision."
            ),
            styles["body"]
        )
    )

    story.append(
        PageBreak()
    )
    _section(
        story,
        "Annexe - chiffres importants a retenir" if language == "fr" else "Appendix - Key Figures to Remember",
        styles
    )
    story.append(
        _table(
            _key_metric_rows(
                portfolio=portfolio,
                spot=spot,
                volatility=volatility,
                scenario_results=scenario_results,
                var_result=var_result,
                parametric_var=parametric_var,
                hedge_result=hedge_result,
                risk_score_result=risk_score_result,
                probabilistic_result=probabilistic_result,
                language=language
            ),
            widths=[
                7.2 * cm,
                8.8 * cm
            ],
        )
    )

    story.append(
        Spacer(
            1,
            12
        )
    )
    story.append(
        _p(
            (
                f"Document genere par ARIA. Developpe par {author_name}."
                if language == "fr"
                else f"Document generated by ARIA. Developed by {author_name}."
            ),
            styles["small"]
        )
    )

    doc.build(
        story,
        onFirstPage=lambda canvas, document: _draw_pdf_page(
            canvas,
            document,
            doc_title,
            author_name
        ),
        onLaterPages=lambda canvas, document: _draw_pdf_page(
            canvas,
            document,
            doc_title,
            author_name
        ),
    )
    buffer.seek(
        0
    )

    return buffer.getvalue()


def generate_pdf_report(
    report_text: str,
    author_name: str = AUTHOR_NAME
) -> bytes:
    """Generate a simple PDF document from a Markdown risk report."""

    styles = _pdf_styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.2 * cm,
        title="ARIA Executive Risk Report",
        author=author_name,
    )
    story: list[Any] = [
        Paragraph(
            "ARIA Executive Risk Report",
            styles["cover_title"]
        ),
        _p(
            f"Developed by {author_name}",
            styles["cover_subtitle"]
        ),
    ]

    for raw_line in report_text.splitlines():
        clean_line = _clean_markdown_for_pdf(
            raw_line
        )

        if not clean_line:
            story.append(
                Spacer(
                    1,
                    4
                )
            )
            continue

        if raw_line.startswith(
            "## "
        ) or raw_line.startswith(
            "# "
        ):
            story.append(
                Paragraph(
                    escape(
                        clean_line
                    ),
                    styles["section"]
                )
            )
        else:
            story.append(
                _p(
                    clean_line,
                    styles["body"]
                )
            )

    doc.build(
        story,
        onFirstPage=lambda canvas, document: _draw_pdf_page(
            canvas,
            document,
            "ARIA Executive Risk Report",
            author_name
        ),
        onLaterPages=lambda canvas, document: _draw_pdf_page(
            canvas,
            document,
            "ARIA Executive Risk Report",
            author_name
        ),
    )

    buffer.seek(
        0
    )

    return buffer.getvalue()


if __name__ == "__main__":
    from portfolio_engine.pricing_BS import OptionContract
    from risk_engine.hedging_analysis import calculate_delta_hedge
    from risk_engine.risk_score import calculate_risk_score
    from risk_engine.scenario_analysis import run_standard_scenarios
    from risk_engine.var_analysis import calculate_var_es, parametric_var_estimate

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
        name="Calls achetes"
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

    print(
        generate_risk_report(
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
    )
