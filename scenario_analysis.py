"""
ARIA - Analyse de scénarios et stress tests
"""

from copy import deepcopy
from dataclasses import dataclass

from portfolio import OptionPosition, Portfolio, StockPosition


@dataclass
class ScenarioResult:
    name: str
    spot_change_percent: float
    volatility_change_points: float
    initial_value: float
    stressed_value: float
    profit_and_loss: float
    stressed_delta: float
    stressed_gamma: float
    stressed_vega: float
    rate_change_points: float = 0.0
    correlation_shock: float = 0.0
    description: str = ""
    top_contributors: list[dict[str, float | str]] | None = None


def apply_scenario(
    portfolio: Portfolio,
    spot_change_percent: float,
    volatility_change_points: float,
    rate_change_points: float = 0.0
) -> Portfolio:
    """
    Crée une copie du portefeuille et lui applique un choc de marché.

    Exemple :
    spot_change_percent = -0.05 signifie une baisse du spot de 5 %.
    volatility_change_points = 0.10 signifie une hausse de vol de 10 points.
    """

    stressed_portfolio = deepcopy(portfolio)

    for position in stressed_portfolio.positions:

        if isinstance(position, OptionPosition):
            old_spot = position.contract.S
            old_volatility = position.contract.sigma
            old_rate = position.contract.r

            new_spot = old_spot * (1 + spot_change_percent)
            new_volatility = old_volatility + volatility_change_points
            new_rate = old_rate + rate_change_points

            position.contract.S = new_spot
            position.contract.sigma = max(new_volatility, 0.0001)
            position.contract.r = new_rate

        elif isinstance(position, StockPosition):
            position.spot *= 1 + spot_change_percent

    return stressed_portfolio


def run_scenario(
    portfolio: Portfolio,
    name: str,
    spot_change_percent: float,
    volatility_change_points: float,
    rate_change_points: float = 0.0,
    correlation_shock: float = 0.0,
    description: str = ""
) -> ScenarioResult:
    """Calcule la variation du portefeuille après un choc de marché."""

    initial_value = portfolio.total_market_value()

    stressed_portfolio = apply_scenario(
        portfolio=portfolio,
        spot_change_percent=spot_change_percent,
        volatility_change_points=volatility_change_points,
        rate_change_points=rate_change_points
    )

    stressed_value = stressed_portfolio.total_market_value()
    profit_and_loss = stressed_value - initial_value
    stressed_greeks = stressed_portfolio.total_greeks()
    top_contributors = calculate_position_contributions(
        portfolio=portfolio,
        stressed_portfolio=stressed_portfolio
    )

    return ScenarioResult(
        name=name,
        spot_change_percent=spot_change_percent,
        volatility_change_points=volatility_change_points,
        initial_value=initial_value,
        stressed_value=stressed_value,
        profit_and_loss=profit_and_loss,
        stressed_delta=stressed_greeks["delta"],
        stressed_gamma=stressed_greeks["gamma"],
        stressed_vega=stressed_greeks["vega"],
        rate_change_points=rate_change_points,
        correlation_shock=correlation_shock,
        description=description,
        top_contributors=top_contributors
    )


def calculate_position_contributions(
    portfolio: Portfolio,
    stressed_portfolio: Portfolio
) -> list[dict[str, float | str]]:
    """Return position-level P&L contributions for a scenario."""

    contributions = []

    for initial_position, stressed_position in zip(
        portfolio.positions,
        stressed_portfolio.positions,
        strict=False
    ):
        initial_value = initial_position.market_value()
        stressed_value = stressed_position.market_value()
        pnl = stressed_value - initial_value
        contributions.append(
            {
                "name": initial_position.name or "Position",
                "underlying": initial_position.underlying,
                "initial_value": initial_value,
                "stressed_value": stressed_value,
                "pnl": pnl,
                "abs_pnl": abs(
                    pnl
                ),
            }
        )

    return sorted(
        contributions,
        key=lambda item: float(
            item["abs_pnl"]
        ),
        reverse=True
    )


def historical_stress_definitions() -> list[dict[str, float | str]]:
    """Return stylized historical crisis scenarios."""

    return [
        {
            "name": "2008 Global Financial Crisis",
            "spot_change_percent": -0.28,
            "volatility_change_points": 0.32,
            "rate_change_points": -0.015,
            "correlation_shock": 0.35,
            "description": "Equity crash, volatility regime break and correlation convergence inspired by 2008.",
        },
        {
            "name": "Covid Liquidity Shock",
            "spot_change_percent": -0.24,
            "volatility_change_points": 0.42,
            "rate_change_points": -0.010,
            "correlation_shock": 0.30,
            "description": "Fast equity sell-off, volatility spike and forced deleveraging inspired by March 2020.",
        },
        {
            "name": "Japan / Yen Carry Unwind",
            "spot_change_percent": -0.16,
            "volatility_change_points": 0.22,
            "rate_change_points": 0.010,
            "correlation_shock": 0.25,
            "description": "Risk-off carry unwind with equity pressure, higher volatility and rates repricing.",
        },
        {
            "name": "Inflation Shock",
            "spot_change_percent": -0.12,
            "volatility_change_points": 0.16,
            "rate_change_points": 0.020,
            "correlation_shock": 0.18,
            "description": "Inflation surprise with rates up, equities down and cross-asset correlation rising.",
        },
        {
            "name": "Rates Shock",
            "spot_change_percent": -0.08,
            "volatility_change_points": 0.10,
            "rate_change_points": 0.030,
            "correlation_shock": 0.12,
            "description": "Abrupt curve repricing and duration shock.",
        },
        {
            "name": "Tech Sell-off",
            "spot_change_percent": -0.22,
            "volatility_change_points": 0.24,
            "rate_change_points": 0.012,
            "correlation_shock": 0.20,
            "description": "Growth and technology factor de-rating with volatility expansion.",
        },
        {
            "name": "Volatility Spike",
            "spot_change_percent": -0.06,
            "volatility_change_points": 0.35,
            "rate_change_points": 0.000,
            "correlation_shock": 0.22,
            "description": "Volatility shock similar to short-vol unwind episodes.",
        },
        {
            "name": "Sovereign / Banking Stress",
            "spot_change_percent": -0.18,
            "volatility_change_points": 0.26,
            "rate_change_points": -0.005,
            "correlation_shock": 0.28,
            "description": "Banking-system stress with equity drawdown, volatility jump and flight to quality.",
        },
    ]


def run_historical_scenarios(
    portfolio: Portfolio
) -> list[ScenarioResult]:
    """Run stylized historical crisis stress tests."""

    return [
        run_scenario(
            portfolio=portfolio,
            name=str(
                scenario["name"]
            ),
            spot_change_percent=float(
                scenario["spot_change_percent"]
            ),
            volatility_change_points=float(
                scenario["volatility_change_points"]
            ),
            rate_change_points=float(
                scenario["rate_change_points"]
            ),
            correlation_shock=float(
                scenario["correlation_shock"]
            ),
            description=str(
                scenario["description"]
            ),
        )
        for scenario in historical_stress_definitions()
    ]


def run_standard_scenarios(
    portfolio: Portfolio
) -> list[ScenarioResult]:
    """Lance plusieurs scénarios de marché prédéfinis."""

    scenarios = [
        {
            "name": "Hausse modérée",
            "spot_change_percent": 0.05,
            "volatility_change_points": -0.02
        },
        {
            "name": "Baisse modérée",
            "spot_change_percent": -0.05,
            "volatility_change_points": 0.05
        },
        {
            "name": "Stress de marché",
            "spot_change_percent": -0.10,
            "volatility_change_points": 0.15
        },
        {
            "name": "Chute de volatilité",
            "spot_change_percent": 0.0,
            "volatility_change_points": -0.10
        },
        {
            "name": "Explosion de volatilité",
            "spot_change_percent": 0.0,
            "volatility_change_points": 0.20
        }
    ]

    results = []

    for scenario in scenarios:
        result = run_scenario(
            portfolio=portfolio,
            name=scenario["name"],
            spot_change_percent=scenario["spot_change_percent"],
            volatility_change_points=scenario[
                "volatility_change_points"
            ]
        )

        results.append(result)

    return results


def display_results(
    results: list[ScenarioResult]
) -> None:
    """Affiche les résultats dans le terminal."""

    print("ARIA - Analyse de scénarios")

    for result in results:
        print(f"\nScénario : {result.name}")
        print(
            f"Variation du spot : "
            f"{result.spot_change_percent:.2%}"
        )
        print(
            f"Variation de volatilité : "
            f"{result.volatility_change_points:.2%}"
        )
        print(
            f"Valeur initiale : "
            f"{result.initial_value:.2f}"
        )
        print(
            f"Valeur stressée : "
            f"{result.stressed_value:.2f}"
        )
        print(
            f"Profit / perte : "
            f"{result.profit_and_loss:.2f}"
        )
        print(
            f"Delta après choc : "
            f"{result.stressed_delta:.4f}"
        )
        print(
            f"Gamma après choc : "
            f"{result.stressed_gamma:.4f}"
        )
        print(
            f"Vega après choc : "
            f"{result.stressed_vega:.4f}"
        )


if __name__ == "__main__":
    from pricing_BS import OptionContract

    portfolio = Portfolio(
        name="Portefeuille de stress test"
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

    scenario_results = run_standard_scenarios(
        portfolio
    )

    display_results(
        scenario_results
    )
