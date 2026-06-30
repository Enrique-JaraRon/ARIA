"""
ARIA - Executive risk report generation.
"""

from datetime import datetime
from typing import Any

from portfolio import Portfolio


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
        f"| ARIA Risk Score | {risk_score_result.score}/100 - {risk_score_result.label} |",
        f"| Quantitative alerts | {len(alerts)} |",
        f"| VaR | {format_number(var_result.var_amount)} |",
        f"| Expected Shortfall | {format_number(var_result.expected_shortfall)} |",
    ]

    if worst_scenario is not None:
        lines.append(
            f"| Worst stress scenario | {worst_scenario.name} "
            f"({format_number(worst_scenario.profit_and_loss)}) |"
        )

    if best_scenario is not None:
        lines.append(
            f"| Best stress scenario | {best_scenario.name} "
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
        f"**Status:** {risk_score_result.label}",
        "",
        risk_score_result.explanation,
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
            f"{result.name} | "
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
                f"Best scenario: **{best_scenario.name}** with P&L "
                f"**{format_number(best_scenario.profit_and_loss)}**."
            ),
            (
                f"Worst scenario: **{worst_scenario.name}** with P&L "
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
            f"- Worst stress scenario: {worst_scenario.name} "
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
            "- Consider reducing concentrated exposures or tightening monitoring frequency."
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
    Generate a complete Markdown executive risk report.
    """

    report_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    lines = [
        "# ARIA Executive Risk Report",
        "",
        f"Generated at: **{report_date}**",
        "",
        generate_executive_summary_section(
            portfolio=portfolio,
            spot=spot,
            volatility=volatility,
            alerts=alerts,
            scenario_results=scenario_results,
            var_result=var_result,
            risk_score_result=risk_score_result
        ),
        generate_market_section(
            market_snapshot
        ),
        generate_portfolio_overview_section(
            portfolio
        ),
        generate_risk_score_section(
            risk_score_result
        ),
        generate_greeks_section(
            portfolio
        ),
        generate_stress_section(
            scenario_results
        ),
        generate_var_section(
            var_result,
            parametric_var
        ),
        generate_hedge_section(
            hedge_result
        ),
        generate_key_risk_drivers_section(
            risk_score_result=risk_score_result,
            scenario_results=scenario_results,
            var_result=var_result
        ),
        generate_alerts_section(
            alerts
        ),
        generate_llm_section(
            llm_analysis
        ),
        generate_limitations_section(),
        generate_recommended_actions_section(
            alerts=alerts,
            risk_score_result=risk_score_result,
            hedge_result=hedge_result
        ),
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
    market_snapshot: Any | None = None,
    llm_analysis: str | None = None
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
        hedge_result=hedge_result,
        risk_score_result=risk_score_result,
        market_snapshot=market_snapshot,
        llm_analysis=llm_analysis
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
