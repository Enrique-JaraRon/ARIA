"""
ARIA - Probabilistic portfolio risk analysis.

The LLM is not used in this module. All probabilities, VaR, Expected
Shortfall and downside contributions are computed quantitatively.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from portfolio import OptionPosition, Portfolio, StockPosition
from pricing_BS import OptionContract, bs_price


@dataclass
class PositionRiskContribution:
    """Position contribution to simulated downside risk."""

    name: str
    underlying: str
    average_tail_pnl: float
    downside_contribution: float
    contribution_percent: float


@dataclass
class ProbabilisticRiskResult:
    """Summary of a Monte Carlo probabilistic risk analysis."""

    horizon_days: int
    number_of_simulations: int
    confidence_level: float
    portfolio_value: float
    exposure_base: float
    probability_of_loss: float
    probability_loss_gt_5: float
    probability_loss_gt_10: float
    probability_loss_gt_20: float
    mean_return: float
    simulated_volatility: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    worst_return: float
    best_return: float
    worst_loss_amount: float
    best_gain_amount: float
    top_contributors: list[PositionRiskContribution]
    main_risk_driver: str
    interpretation: str


def _position_value_after_return(
    position,
    underlying_return: float,
    horizon_days: int
) -> float:
    """Reprice one position after an underlying return shock."""

    if isinstance(
        position,
        StockPosition
    ):
        stressed_spot = position.spot * (
            1 + underlying_return
        )
        return stressed_spot * position.quantity

    if isinstance(
        position,
        OptionPosition
    ):
        contract = position.contract
        stressed_contract = OptionContract(
            S=max(
                contract.S * (
                    1 + underlying_return
                ),
                0.0001
            ),
            K=contract.K,
            T=max(
                contract.T - horizon_days / 365,
                1 / 365
            ),
            r=contract.r,
            sigma=contract.sigma,
            option_type=contract.option_type,
            q=contract.q
        )
        return (
            bs_price(
                stressed_contract
            )
            * position.quantity
            * position.multiplier
        )

    raise TypeError(
        "Unsupported position type."
    )


def _portfolio_exposure_base(
    portfolio: Portfolio
) -> float:
    """Return a stable denominator for return-like risk metrics."""

    net_value = abs(
        portfolio.total_market_value()
    )
    gross_value = sum(
        abs(
            position.market_value()
        )
        for position in portfolio.positions
    )

    return max(
        net_value,
        gross_value,
        1.0
    )


def _estimate_underlying_statistics(
    portfolio: Portfolio,
    historical_returns: pd.DataFrame | None = None
) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """Estimate annual mean, annual volatility and correlation."""

    underlyings = portfolio.underlyings()

    if not underlyings:
        raise ValueError(
            "The portfolio must contain at least one underlying."
        )

    if historical_returns is not None and not historical_returns.empty:
        available = [
            underlying
            for underlying in underlyings
            if underlying in historical_returns.columns
        ]

        if available:
            returns = historical_returns[
                available
            ].dropna()
            annual_mean = returns.mean().to_numpy() * 252
            annual_volatility = returns.std(ddof=0).to_numpy() * np.sqrt(
                252
            )
            correlation = returns.corr().fillna(
                0.0
            ).to_numpy()
            correlation = np.nan_to_num(
                correlation,
                nan=0.0
            )
            np.fill_diagonal(
                correlation,
                1.0
            )
            return (
                available,
                annual_mean,
                np.maximum(
                    annual_volatility,
                    0.0001
                ),
                correlation
            )

    annual_mean_by_underlying = {}
    annual_vol_by_underlying = {}

    for underlying in underlyings:
        vols = []

        for position in portfolio.positions:
            if position.underlying != underlying:
                continue

            if isinstance(
                position,
                OptionPosition
            ):
                vols.append(
                    position.contract.sigma
                )

        annual_mean_by_underlying[underlying] = 0.05
        annual_vol_by_underlying[underlying] = (
            float(
                np.mean(
                    vols
                )
            )
            if vols
            else 0.20
        )

    annual_mean = np.array(
        [
            annual_mean_by_underlying[underlying]
            for underlying in underlyings
        ],
        dtype=float
    )
    annual_volatility = np.array(
        [
            annual_vol_by_underlying[underlying]
            for underlying in underlyings
        ],
        dtype=float
    )

    correlation = np.full(
        (
            len(
                underlyings
            ),
            len(
                underlyings
            )
        ),
        0.35
    )
    np.fill_diagonal(
        correlation,
        1.0
    )

    return (
        underlyings,
        annual_mean,
        annual_volatility,
        correlation
    )


def _nearest_positive_semidefinite(
    matrix: np.ndarray
) -> np.ndarray:
    """Make a correlation matrix numerically usable."""

    symmetric = (
        matrix + matrix.T
    ) / 2
    eigenvalues, eigenvectors = np.linalg.eigh(
        symmetric
    )
    eigenvalues = np.clip(
        eigenvalues,
        0.0001,
        None
    )
    adjusted = (
        eigenvectors
        @ np.diag(
            eigenvalues
        )
        @ eigenvectors.T
    )
    diagonal = np.sqrt(
        np.diag(
            adjusted
        )
    )
    adjusted = adjusted / np.outer(
        diagonal,
        diagonal
    )
    np.fill_diagonal(
        adjusted,
        1.0
    )
    return adjusted


def _var_and_es(
    returns: np.ndarray,
    confidence_level: float
) -> tuple[float, float]:
    """Return lower-tail VaR and Expected Shortfall as returns."""

    tail_probability = 1 - confidence_level
    var_level = float(
        np.quantile(
            returns,
            tail_probability
        )
    )
    tail_returns = returns[
        returns <= var_level
    ]
    expected_shortfall = (
        float(
            tail_returns.mean()
        )
        if len(
            tail_returns
        )
        else var_level
    )
    return var_level, expected_shortfall


def _calculate_contributions(
    portfolio: Portfolio,
    simulations: pd.DataFrame,
    position_pnl_matrix: np.ndarray,
    var_95: float
) -> list[PositionRiskContribution]:
    """Estimate position contributions in the 5% lower tail."""

    tail_mask = simulations[
        "Portfolio return"
    ].to_numpy() <= var_95

    if not tail_mask.any():
        return []

    average_tail_pnl = position_pnl_matrix[
        tail_mask
    ].mean(
        axis=0
    )
    downside_amounts = np.maximum(
        -average_tail_pnl,
        0
    )
    total_downside = float(
        downside_amounts.sum()
    )

    contributions = []

    for index, position in enumerate(
        portfolio.positions
    ):
        contribution = float(
            downside_amounts[
                index
            ]
        )
        contribution_percent = (
            contribution / total_downside
            if total_downside > 0
            else 0.0
        )
        contributions.append(
            PositionRiskContribution(
                name=position.name or f"Position {index + 1}",
                underlying=position.underlying,
                average_tail_pnl=float(
                    average_tail_pnl[
                        index
                    ]
                ),
                downside_contribution=contribution,
                contribution_percent=contribution_percent
            )
        )

    return sorted(
        contributions,
        key=lambda contribution: contribution.downside_contribution,
        reverse=True
    )


def simulate_probabilistic_risk(
    portfolio: Portfolio,
    horizon_days: int = 21,
    number_of_simulations: int = 5000,
    confidence_level: float = 0.95,
    historical_returns: pd.DataFrame | None = None,
    seed: int = 42
) -> tuple[ProbabilisticRiskResult, pd.DataFrame]:
    """Run Monte Carlo probabilistic risk analysis."""

    if horizon_days <= 0:
        raise ValueError(
            "horizon_days must be positive."
        )

    if number_of_simulations < 100:
        raise ValueError(
            "number_of_simulations must be at least 100."
        )

    if confidence_level not in {
        0.95,
        0.99
    }:
        raise ValueError(
            "confidence_level must be 0.95 or 0.99."
        )

    underlyings, annual_mean, annual_volatility, correlation = (
        _estimate_underlying_statistics(
            portfolio=portfolio,
            historical_returns=historical_returns
        )
    )
    correlation = _nearest_positive_semidefinite(
        correlation
    )

    horizon_scale = horizon_days / 252
    horizon_mean = annual_mean * horizon_scale
    horizon_covariance = (
        np.outer(
            annual_volatility,
            annual_volatility
        )
        * correlation
        * horizon_scale
    )

    rng = np.random.default_rng(
        seed
    )
    simulated_underlying_returns = rng.multivariate_normal(
        mean=horizon_mean,
        cov=horizon_covariance,
        size=number_of_simulations
    )

    initial_position_values = np.array(
        [
            position.market_value()
            for position in portfolio.positions
        ],
        dtype=float
    )
    initial_value = float(
        initial_position_values.sum()
    )
    exposure_base = _portfolio_exposure_base(
        portfolio
    )

    position_pnl_matrix = np.zeros(
        (
            number_of_simulations,
            len(
                portfolio.positions
            )
        )
    )
    portfolio_pnl = np.zeros(
        number_of_simulations
    )

    underlying_index = {
        underlying: index
        for index, underlying in enumerate(
            underlyings
        )
    }

    records = []

    for simulation_index in range(
        number_of_simulations
    ):
        return_vector = simulated_underlying_returns[
            simulation_index
        ]
        return_map = {
            underlying: float(
                return_vector[
                    index
                ]
            )
            for underlying, index in underlying_index.items()
        }

        stressed_values = []

        for position_index, position in enumerate(
            portfolio.positions
        ):
            underlying_return = return_map.get(
                position.underlying,
                0.0
            )
            stressed_value = _position_value_after_return(
                position=position,
                underlying_return=underlying_return,
                horizon_days=horizon_days
            )
            pnl = stressed_value - initial_position_values[
                position_index
            ]
            position_pnl_matrix[
                simulation_index,
                position_index
            ] = pnl
            stressed_values.append(
                stressed_value
            )

        pnl_total = float(
            np.sum(
                position_pnl_matrix[
                    simulation_index
                ]
            )
        )
        portfolio_pnl[
            simulation_index
        ] = pnl_total

        record = {
            "Simulation": simulation_index + 1,
            "Portfolio P&L": pnl_total,
            "Portfolio return": pnl_total / exposure_base,
            "Stressed value": initial_value + pnl_total,
        }
        for underlying in underlyings:
            record[
                f"{underlying} return"
            ] = return_map[
                underlying
            ]
        records.append(
            record
        )

    simulations = pd.DataFrame(
        records
    )
    portfolio_returns = simulations[
        "Portfolio return"
    ].to_numpy()

    var_95, expected_shortfall_95 = _var_and_es(
        portfolio_returns,
        0.95
    )
    var_99, expected_shortfall_99 = _var_and_es(
        portfolio_returns,
        0.99
    )

    top_contributors = _calculate_contributions(
        portfolio=portfolio,
        simulations=simulations,
        position_pnl_matrix=position_pnl_matrix,
        var_95=var_95
    )
    main_driver = (
        f"{top_contributors[0].name} ({top_contributors[0].underlying})"
        if top_contributors
        else "Not available"
    )

    probability_of_loss = float(
        np.mean(
            portfolio_returns < 0
        )
    )
    result = ProbabilisticRiskResult(
        horizon_days=horizon_days,
        number_of_simulations=number_of_simulations,
        confidence_level=confidence_level,
        portfolio_value=initial_value,
        exposure_base=exposure_base,
        probability_of_loss=probability_of_loss,
        probability_loss_gt_5=float(
            np.mean(
                portfolio_returns <= -0.05
            )
        ),
        probability_loss_gt_10=float(
            np.mean(
                portfolio_returns <= -0.10
            )
        ),
        probability_loss_gt_20=float(
            np.mean(
                portfolio_returns <= -0.20
            )
        ),
        mean_return=float(
            portfolio_returns.mean()
        ),
        simulated_volatility=float(
            portfolio_returns.std(
                ddof=0
            )
        ),
        var_95=var_95,
        var_99=var_99,
        expected_shortfall_95=expected_shortfall_95,
        expected_shortfall_99=expected_shortfall_99,
        worst_return=float(
            portfolio_returns.min()
        ),
        best_return=float(
            portfolio_returns.max()
        ),
        worst_loss_amount=float(
            -portfolio_pnl.min()
        ),
        best_gain_amount=float(
            portfolio_pnl.max()
        ),
        top_contributors=top_contributors,
        main_risk_driver=main_driver,
        interpretation=build_probabilistic_risk_report_text(
            probability_of_loss=probability_of_loss,
            var_95=var_95,
            expected_shortfall_95=expected_shortfall_95,
            main_driver=main_driver
        )
    )

    return result, simulations


def build_probabilistic_risk_report_text(
    probability_of_loss: float,
    var_95: float,
    expected_shortfall_95: float,
    main_driver: str
) -> str:
    """Build a simple client-ready explanation from computed numbers."""

    return (
        "Selon les hypotheses du modele, le portefeuille presente une "
        f"probabilite estimee de perte de {probability_of_loss:.1%}. "
        f"La VaR 95% est de {var_95:.1%}, ce qui signifie que 95% des "
        "simulations font mieux que ce seuil sur l'horizon choisi. "
        f"L'Expected Shortfall 95% est de {expected_shortfall_95:.1%}: dans "
        "les 5% de simulations les plus defavorables, la perte moyenne est "
        "proche de ce niveau. "
        f"Le principal moteur de risque identifie est {main_driver}. "
        "Ces probabilites ne sont pas des predictions certaines; elles "
        "dependent des donnees, de la volatilite, des correlations et des "
        "hypotheses de simulation."
    )


def probabilistic_metrics_table(
    result: ProbabilisticRiskResult
) -> pd.DataFrame:
    """Return a compact metrics table for Streamlit or reports."""

    return pd.DataFrame(
        [
            {
                "Metric": "Probability of loss",
                "Value": result.probability_of_loss,
                "Format": "percent",
            },
            {
                "Metric": "Probability of loss > 5%",
                "Value": result.probability_loss_gt_5,
                "Format": "percent",
            },
            {
                "Metric": "Probability of loss > 10%",
                "Value": result.probability_loss_gt_10,
                "Format": "percent",
            },
            {
                "Metric": "Probability of loss > 20%",
                "Value": result.probability_loss_gt_20,
                "Format": "percent",
            },
            {
                "Metric": "Mean simulated return",
                "Value": result.mean_return,
                "Format": "percent",
            },
            {
                "Metric": "Simulated volatility",
                "Value": result.simulated_volatility,
                "Format": "percent",
            },
            {
                "Metric": "VaR 95%",
                "Value": result.var_95,
                "Format": "percent",
            },
            {
                "Metric": "Expected Shortfall 95%",
                "Value": result.expected_shortfall_95,
                "Format": "percent",
            },
            {
                "Metric": "VaR 99%",
                "Value": result.var_99,
                "Format": "percent",
            },
            {
                "Metric": "Expected Shortfall 99%",
                "Value": result.expected_shortfall_99,
                "Format": "percent",
            },
            {
                "Metric": "Worst simulated return",
                "Value": result.worst_return,
                "Format": "percent",
            },
            {
                "Metric": "Best simulated return",
                "Value": result.best_return,
                "Format": "percent",
            },
        ]
    )


def contribution_table(
    result: ProbabilisticRiskResult
) -> pd.DataFrame:
    """Return downside contribution table."""

    return pd.DataFrame(
        [
            {
                "Position": contribution.name,
                "Underlying": contribution.underlying,
                "Average tail P&L": contribution.average_tail_pnl,
                "Downside contribution": contribution.downside_contribution,
                "Contribution %": contribution.contribution_percent,
            }
            for contribution in result.top_contributors
        ]
    )
