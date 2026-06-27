"""
ARIA - Données de marché Yahoo Finance
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class MarketSnapshot:
    """Représente un snapshot de marché récupéré en ligne."""

    ticker: str
    last_price: float
    previous_price: float
    daily_return: float
    annualized_volatility: float
    number_of_observations: int


def get_market_snapshot(
    ticker: str,
    period: str = "6mo"
) -> MarketSnapshot:
    """
    Récupère les données de marché depuis Yahoo Finance.

    La volatilité est calculée comme la volatilité historique annualisée
    des rendements journaliers.
    """

    if not ticker.strip():
        raise ValueError(
            "Le ticker ne peut pas être vide."
        )

    try:
        import yfinance as yf

    except ImportError as error:
        raise ImportError(
            "Le module yfinance n'est pas installé. "
            "Installe-le avec : pip install yfinance"
        ) from error

    clean_ticker = ticker.strip().upper()

    data = yf.download(
        clean_ticker,
        period=period,
        progress=False,
        auto_adjust=True
    )

    if data.empty:
        raise ValueError(
            f"Aucune donnée trouvée pour le ticker {clean_ticker}."
        )

    if isinstance(
        data.columns,
        pd.MultiIndex
    ):
        data.columns = data.columns.get_level_values(
            0
        )

    if "Close" not in data.columns:
        raise ValueError(
            "La colonne Close est introuvable dans les données."
        )

    close_prices = data["Close"].dropna()

    if len(close_prices) < 3:
        raise ValueError(
            "Pas assez de données pour calculer la volatilité."
        )

    last_price = float(
        close_prices.iloc[-1]
    )

    previous_price = float(
        close_prices.iloc[-2]
    )

    daily_return = (
        last_price
        / previous_price
        - 1
    )

    returns = close_prices.pct_change().dropna()

    annualized_volatility = float(
        returns.std()
        * (252 ** 0.5)
    )

    if annualized_volatility <= 0:
        raise ValueError(
            "La volatilité calculée est invalide."
        )

    return MarketSnapshot(
        ticker=clean_ticker,
        last_price=last_price,
        previous_price=previous_price,
        daily_return=daily_return,
        annualized_volatility=annualized_volatility,
        number_of_observations=len(close_prices)
    )


if __name__ == "__main__":

    snapshot = get_market_snapshot(
        ticker="SPY"
    )

    print("Snapshot de marché")
    print(f"Ticker : {snapshot.ticker}")
    print(f"Dernier prix : {snapshot.last_price:.2f}")
    print(f"Prix précédent : {snapshot.previous_price:.2f}")
    print(f"Rendement journalier : {snapshot.daily_return:.2%}")
    print(f"Volatilité annualisée : {snapshot.annualized_volatility:.2%}")
    print(f"Observations : {snapshot.number_of_observations}")  