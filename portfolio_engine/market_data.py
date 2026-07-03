"""
ARIA - Market data provider architecture.

Yahoo Finance remains the default demo provider. CSV and manual providers make
ARIA usable offline, while Bloomberg is represented as an optional professional
integration that only activates when the Bloomberg stack is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


@dataclass
class MarketSnapshot:
    """Represents a normalized market snapshot used by ARIA."""

    ticker: str
    last_price: float
    previous_price: float
    daily_return: float
    annualized_volatility: float
    number_of_observations: int
    source: str = "Yahoo Finance"
    status: str = "OK"
    timestamp: str | None = None


@dataclass
class HistoricalMarketData:
    """Normalized historical market data for several underlyings."""

    tickers: list[str]
    prices: pd.DataFrame
    returns: pd.DataFrame
    snapshots: dict[str, MarketSnapshot]
    failed_tickers: dict[str, str]
    source: str
    status: str
    timestamp: str

    @property
    def number_of_observations(self) -> int:
        """Return the number of usable historical return observations."""

        return len(
            self.returns
        )

    def correlation_matrix(self) -> pd.DataFrame:
        """Return the return-correlation matrix."""

        if self.returns.empty:
            return pd.DataFrame()

        return self.returns.corr().fillna(
            0.0
        )


class MarketDataProvider:
    """Base class for market data providers."""

    source_name = "Market Data Provider"

    def get_market_snapshot(
        self,
        ticker: str
    ) -> MarketSnapshot:
        """Return a normalized market snapshot for a ticker."""

        raise NotImplementedError

    def get_historical_data(
        self,
        tickers: list[str]
    ) -> HistoricalMarketData:
        """Return historical market data for several tickers."""

        return _history_from_snapshots(
            provider=self,
            tickers=tickers,
        )


def _utc_timestamp() -> str:
    """Return an ISO timestamp for provider snapshots."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def _clean_ticker(
    ticker: str
) -> str:
    """Normalize and validate a ticker."""

    clean = ticker.strip().upper()

    if not clean:
        raise ValueError(
            "Le ticker ne peut pas etre vide."
        )

    return clean


def _clean_tickers(
    tickers: list[str]
) -> list[str]:
    """Normalize, deduplicate and validate a ticker list."""

    cleaned = []

    for ticker in tickers:
        clean = _clean_ticker(
            str(
                ticker
            )
        )
        if clean not in cleaned:
            cleaned.append(
                clean
            )

    if not cleaned:
        raise ValueError(
            "Au moins un ticker est necessaire."
        )

    return cleaned


def _snapshot_from_close_prices(
    ticker: str,
    close_prices: pd.Series,
    source: str,
    status: str = "OK"
) -> MarketSnapshot:
    """Build a MarketSnapshot from a clean close-price series."""

    clean_prices = close_prices.dropna().astype(
        float
    )

    if len(clean_prices) < 3:
        raise ValueError(
            "Pas assez de donnees pour calculer la volatilite."
        )

    last_price = float(
        clean_prices.iloc[-1]
    )
    previous_price = float(
        clean_prices.iloc[-2]
    )
    daily_return = (
        last_price
        / previous_price
        - 1
    )
    returns = clean_prices.pct_change().dropna()
    annualized_volatility = float(
        returns.std()
        * (252 ** 0.5)
    )

    if annualized_volatility <= 0:
        raise ValueError(
            "La volatilite calculee est invalide."
        )

    return MarketSnapshot(
        ticker=ticker,
        last_price=last_price,
        previous_price=previous_price,
        daily_return=daily_return,
        annualized_volatility=annualized_volatility,
        number_of_observations=len(clean_prices),
        source=source,
        status=status,
        timestamp=_utc_timestamp(),
    )


def _history_from_price_frame(
    tickers: list[str],
    close_prices: pd.DataFrame,
    source: str,
    status: str = "OK"
) -> HistoricalMarketData:
    """Build HistoricalMarketData from close-price columns."""

    clean_tickers = _clean_tickers(
        tickers
    )
    prices = close_prices.copy()

    if isinstance(
        prices,
        pd.Series
    ):
        prices = prices.to_frame(
            name=clean_tickers[0]
        )

    prices.columns = [
        str(
            column
        ).upper()
        for column in prices.columns
    ]
    prices = prices.reindex(
        columns=clean_tickers
    )
    prices = prices.apply(
        pd.to_numeric,
        errors="coerce"
    ).dropna(
        how="all"
    )

    snapshots = {}
    failed_tickers = {}
    valid_columns = []

    for ticker in clean_tickers:
        try:
            snapshot = _snapshot_from_close_prices(
                ticker=ticker,
                close_prices=prices[ticker],
                source=source,
                status=status,
            )
            snapshots[ticker] = snapshot
            valid_columns.append(
                ticker
            )

        except Exception as error:
            failed_tickers[ticker] = str(
                error
            )

    valid_prices = prices[
        valid_columns
    ].dropna(
        how="all"
    ) if valid_columns else pd.DataFrame()
    returns = valid_prices.pct_change(
        fill_method=None
    ).dropna(
        how="all"
    )

    history_status = (
        status
        if not failed_tickers
        else "Partiel"
    )

    return HistoricalMarketData(
        tickers=valid_columns,
        prices=valid_prices,
        returns=returns,
        snapshots=snapshots,
        failed_tickers=failed_tickers,
        source=source,
        status=history_status,
        timestamp=_utc_timestamp(),
    )


def _history_from_snapshots(
    provider: MarketDataProvider,
    tickers: list[str]
) -> HistoricalMarketData:
    """Fallback history builder for providers without real historical prices."""

    clean_tickers = _clean_tickers(
        tickers
    )
    snapshots = {}
    failed_tickers = {}
    prices = {}

    for ticker in clean_tickers:
        try:
            snapshot = provider.get_market_snapshot(
                ticker=ticker
            )
            snapshots[ticker] = snapshot
            prices[ticker] = [
                snapshot.previous_price,
                snapshot.last_price,
            ]

        except Exception as error:
            failed_tickers[ticker] = str(
                error
            )

    price_frame = pd.DataFrame(
        prices
    )
    returns = price_frame.pct_change(
        fill_method=None
    ).dropna(
        how="all"
    )

    return HistoricalMarketData(
        tickers=list(
            snapshots
        ),
        prices=price_frame,
        returns=returns,
        snapshots=snapshots,
        failed_tickers=failed_tickers,
        source=provider.source_name,
        status="Partiel" if failed_tickers else provider.source_name,
        timestamp=_utc_timestamp(),
    )


def _extract_close_prices_from_yahoo(
    data: pd.DataFrame,
    tickers: list[str]
) -> pd.DataFrame:
    """Extract a close-price table from Yahoo Finance output."""

    clean_tickers = _clean_tickers(
        tickers
    )

    if isinstance(
        data.columns,
        pd.MultiIndex
    ):
        first_level = [
            str(
                value
            )
            for value in data.columns.get_level_values(
                0
            )
        ]
        last_level = [
            str(
                value
            )
            for value in data.columns.get_level_values(
                -1
            )
        ]

        if "Close" in first_level:
            close_prices = data[
                "Close"
            ]

        elif "Close" in last_level:
            close_prices = data.xs(
                "Close",
                axis=1,
                level=-1,
            )

        else:
            raise ValueError(
                "La colonne Close est introuvable dans les donnees."
            )

    else:
        if "Close" not in data.columns:
            raise ValueError(
                "La colonne Close est introuvable dans les donnees."
            )
        close_prices = data[
            [
                "Close"
            ]
        ].rename(
            columns={
                "Close": clean_tickers[0]
            }
        )

    if isinstance(
        close_prices,
        pd.Series
    ):
        close_prices = close_prices.to_frame(
            name=clean_tickers[0]
        )

    return close_prices


class ManualMarketDataProvider(MarketDataProvider):
    """Provider used when market values are entered manually."""

    source_name = "Manual Mode"

    def __init__(
        self,
        spot: float,
        volatility: float,
        previous_price: float | None = None
    ) -> None:
        self.spot = spot
        self.volatility = volatility
        self.previous_price = previous_price or spot

    def get_market_snapshot(
        self,
        ticker: str
    ) -> MarketSnapshot:
        """Return a snapshot from manually entered values."""

        clean = _clean_ticker(
            ticker
        )
        daily_return = (
            self.spot
            / self.previous_price
            - 1
            if self.previous_price
            else 0.0
        )

        return MarketSnapshot(
            ticker=clean,
            last_price=float(self.spot),
            previous_price=float(self.previous_price),
            daily_return=float(daily_return),
            annualized_volatility=float(self.volatility),
            number_of_observations=1,
            source=self.source_name,
            status="Manual Mode",
            timestamp=_utc_timestamp(),
        )

    def get_historical_data(
        self,
        tickers: list[str]
    ) -> HistoricalMarketData:
        """Return a minimal manual history for all requested tickers."""

        clean_tickers = _clean_tickers(
            tickers
        )
        snapshots = {
            ticker: self.get_market_snapshot(
                ticker=ticker
            )
            for ticker in clean_tickers
        }
        prices = pd.DataFrame(
            {
                ticker: [
                    snapshot.previous_price,
                    snapshot.last_price,
                ]
                for ticker, snapshot in snapshots.items()
            }
        )
        returns = prices.pct_change(
            fill_method=None
        ).dropna(
            how="all"
        )

        return HistoricalMarketData(
            tickers=clean_tickers,
            prices=prices,
            returns=returns,
            snapshots=snapshots,
            failed_tickers={},
            source=self.source_name,
            status="Manual Mode",
            timestamp=_utc_timestamp(),
        )


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance provider used for demo and public-market data."""

    source_name = "Yahoo Finance"

    def __init__(
        self,
        period: str = "6mo"
    ) -> None:
        self.period = period

    def get_market_snapshot(
        self,
        ticker: str
    ) -> MarketSnapshot:
        """Fetch market data from Yahoo Finance."""

        clean_ticker = _clean_ticker(
            ticker
        )

        try:
            import yfinance as yf

        except ImportError as error:
            raise ImportError(
                "Le module yfinance n'est pas installe. "
                "Installe-le avec : pip install yfinance"
            ) from error

        data = yf.download(
            clean_ticker,
            period=self.period,
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            raise ValueError(
                f"Aucune donnee trouvee pour le ticker {clean_ticker}."
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
                "La colonne Close est introuvable dans les donnees."
            )

        return _snapshot_from_close_prices(
            ticker=clean_ticker,
            close_prices=data["Close"],
            source=self.source_name,
            status="Yahoo Finance",
        )

    def get_historical_data(
        self,
        tickers: list[str]
    ) -> HistoricalMarketData:
        """Fetch historical close prices for several Yahoo tickers."""

        clean_tickers = _clean_tickers(
            tickers
        )

        try:
            import yfinance as yf

        except ImportError as error:
            raise ImportError(
                "Le module yfinance n'est pas installe. "
                "Installe-le avec : pip install yfinance"
            ) from error

        data = yf.download(
            clean_tickers,
            period=self.period,
            progress=False,
            auto_adjust=True,
            group_by="column",
            threads=False,
        )

        if data.empty:
            raise ValueError(
                "Aucune donnee trouvee pour les tickers demandes."
            )

        close_prices = _extract_close_prices_from_yahoo(
            data=data,
            tickers=clean_tickers,
        )

        return _history_from_price_frame(
            tickers=clean_tickers,
            close_prices=close_prices,
            source=self.source_name,
            status="Yahoo Finance",
        )


class CsvMarketDataProvider(MarketDataProvider):
    """Market data provider backed by a local CSV file."""

    source_name = "CSV Provider"

    def __init__(
        self,
        csv_path: str | Path,
        price_column: str = "Close",
        ticker_column: str = "Ticker",
        date_column: str = "Date",
    ) -> None:
        self.csv_path = Path(
            csv_path
        )
        self.price_column = price_column
        self.ticker_column = ticker_column
        self.date_column = date_column

    def get_market_snapshot(
        self,
        ticker: str
    ) -> MarketSnapshot:
        """Load market data from CSV and return a normalized snapshot."""

        clean_ticker = _clean_ticker(
            ticker
        )

        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Fichier CSV introuvable : {self.csv_path}"
            )

        data = pd.read_csv(
            self.csv_path
        )

        if self.ticker_column in data.columns:
            data = data[
                data[self.ticker_column].astype(
                    str
                ).str.upper()
                == clean_ticker
            ]

        if data.empty:
            raise ValueError(
                f"Aucune donnee CSV trouvee pour {clean_ticker}."
            )

        if self.date_column in data.columns:
            data = data.sort_values(
                self.date_column
            )

        if self.price_column not in data.columns:
            raise ValueError(
                f"Colonne de prix introuvable : {self.price_column}"
            )

        return _snapshot_from_close_prices(
            ticker=clean_ticker,
            close_prices=data[self.price_column],
            source=self.source_name,
            status="CSV Provider",
        )

    def get_historical_data(
        self,
        tickers: list[str]
    ) -> HistoricalMarketData:
        """Load historical data from CSV for several tickers."""

        clean_tickers = _clean_tickers(
            tickers
        )

        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Fichier CSV introuvable : {self.csv_path}"
            )

        data = pd.read_csv(
            self.csv_path
        )

        if self.price_column not in data.columns:
            raise ValueError(
                f"Colonne de prix introuvable : {self.price_column}"
            )

        if self.date_column in data.columns:
            data = data.sort_values(
                self.date_column
            )

        if self.ticker_column in data.columns:
            data[self.ticker_column] = (
                data[self.ticker_column]
                .astype(
                    str
                )
                .str.upper()
            )
            filtered = data[
                data[self.ticker_column].isin(
                    clean_tickers
                )
            ]
            if filtered.empty:
                raise ValueError(
                    "Aucune donnee CSV trouvee pour les tickers demandes."
                )

            if self.date_column in filtered.columns:
                close_prices = filtered.pivot_table(
                    index=self.date_column,
                    columns=self.ticker_column,
                    values=self.price_column,
                    aggfunc="last",
                )

            else:
                indexed = filtered.copy()
                indexed["_row"] = indexed.groupby(
                    self.ticker_column
                ).cumcount()
                close_prices = indexed.pivot_table(
                    index="_row",
                    columns=self.ticker_column,
                    values=self.price_column,
                    aggfunc="last",
                )

        else:
            if len(
                clean_tickers
            ) > 1:
                raise ValueError(
                    "Un CSV sans colonne Ticker ne peut alimenter qu'un seul sous-jacent."
                )
            close_prices = data[
                [
                    self.price_column
                ]
            ].rename(
                columns={
                    self.price_column: clean_tickers[0]
                }
            )

        return _history_from_price_frame(
            tickers=clean_tickers,
            close_prices=close_prices,
            source=self.source_name,
            status="CSV Provider",
        )


class BloombergProvider(MarketDataProvider):
    """Optional Bloomberg provider placeholder for professional setups."""

    source_name = "Bloomberg"

    def get_market_snapshot(
        self,
        ticker: str
    ) -> MarketSnapshot:
        """Return a Bloomberg snapshot when Bloomberg API is installed."""

        _clean_ticker(
            ticker
        )

        try:
            import blpapi  # noqa: F401

        except ImportError as error:
            raise ImportError(
                "BloombergProvider necessite Bloomberg Terminal/API "
                "et le package blpapi. ARIA peut fonctionner avec Yahoo "
                "Finance, CSV ou la saisie manuelle dans cet environnement."
            ) from error

        raise NotImplementedError(
            "BloombergProvider est pret pour integration, mais la logique "
            "de session Bloomberg doit etre configuree dans l'environnement "
            "professionnel cible."
        )


def get_provider(
    source: str,
    csv_path: str | Path | None = None,
    spot: float | None = None,
    volatility: float | None = None,
) -> MarketDataProvider:
    """Factory returning a market data provider from a source label."""

    normalized = source.strip().lower()

    if normalized in {
        "manual",
        "manuel",
        "manual mode",
    }:
        if spot is None or volatility is None:
            raise ValueError(
                "Le mode manuel necessite un spot et une volatilite."
            )

        return ManualMarketDataProvider(
            spot=spot,
            volatility=volatility
        )

    if normalized in {
        "yahoo",
        "yahoo finance",
    }:
        return YahooFinanceProvider()

    if normalized in {
        "csv",
        "csv local",
        "csv provider",
    }:
        if csv_path is None:
            raise ValueError(
                "Le provider CSV necessite un chemin de fichier."
            )

        return CsvMarketDataProvider(
            csv_path=csv_path
        )

    if normalized in {
        "bloomberg",
        "bloomberg optionnel",
    }:
        return BloombergProvider()

    raise ValueError(
        f"Source de donnees de marche inconnue : {source}"
    )


def get_market_snapshot(
    ticker: str,
    period: str = "6mo"
) -> MarketSnapshot:
    """
    Backward-compatible helper using Yahoo Finance by default.

    The volatility is calculated as annualized historical volatility from
    daily returns.
    """

    provider = YahooFinanceProvider(
        period=period
    )

    return provider.get_market_snapshot(
        ticker=ticker
    )


if __name__ == "__main__":
    snapshot = get_market_snapshot(
        ticker="SPY"
    )

    print("Snapshot de marche")
    print(f"Source : {snapshot.source}")
    print(f"Statut : {snapshot.status}")
    print(f"Ticker : {snapshot.ticker}")
    print(f"Dernier prix : {snapshot.last_price:.2f}")
    print(f"Prix precedent : {snapshot.previous_price:.2f}")
    print(f"Rendement journalier : {snapshot.daily_return:.2%}")
    print(f"Volatilite annualisee : {snapshot.annualized_volatility:.2%}")
    print(f"Observations : {snapshot.number_of_observations}")
