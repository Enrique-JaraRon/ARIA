"""
Tests du module market_data.py
"""

import sys
import types

import pandas as pd

from market_data import (
    BloombergProvider,
    CsvMarketDataProvider,
    ManualMarketDataProvider,
    get_market_snapshot,
    get_provider,
)


class FakeYFinance:
    """Fausse version de yfinance pour eviter un appel internet."""

    @staticmethod
    def download(
        ticker,
        period="6mo",
        progress=False,
        auto_adjust=True
    ):
        """Renvoie des donnees fictives de marche."""

        dates = pd.date_range(
            start="2024-01-01",
            periods=5,
            freq="D"
        )

        data = pd.DataFrame(
            {
                "Close": [
                    100.0,
                    102.0,
                    101.0,
                    103.0,
                    105.0
                ]
            },
            index=dates
        )

        return data


def test_get_market_snapshot_returns_valid_data(monkeypatch):
    """Verifie que le snapshot de marche est correctement calcule."""

    fake_module = types.ModuleType(
        "yfinance"
    )

    fake_module.download = FakeYFinance.download

    monkeypatch.setitem(
        sys.modules,
        "yfinance",
        fake_module
    )

    snapshot = get_market_snapshot(
        ticker="spy"
    )

    assert snapshot.ticker == "SPY"
    assert snapshot.last_price == 105.0
    assert snapshot.previous_price == 103.0
    assert snapshot.daily_return > 0
    assert snapshot.annualized_volatility > 0
    assert snapshot.number_of_observations == 5
    assert snapshot.source == "Yahoo Finance"


def test_get_market_snapshot_rejects_empty_ticker():
    """Verifie qu'un ticker vide est refuse."""

    try:
        get_market_snapshot(
            ticker=""
        )

    except ValueError as error:
        assert "ticker" in str(error).lower()

    else:
        raise AssertionError(
            "Un ticker vide aurait du provoquer une erreur."
        )


def test_get_market_snapshot_rejects_empty_data(monkeypatch):
    """Verifie qu'une reponse vide de Yahoo Finance est refusee."""

    fake_module = types.ModuleType(
        "yfinance"
    )

    def fake_download(
        ticker,
        period="6mo",
        progress=False,
        auto_adjust=True
    ):
        return pd.DataFrame()

    fake_module.download = fake_download

    monkeypatch.setitem(
        sys.modules,
        "yfinance",
        fake_module
    )

    try:
        get_market_snapshot(
            ticker="UNKNOWN"
        )

    except ValueError as error:
        assert "aucune" in str(error).lower()

    else:
        raise AssertionError(
            "Des donnees vides auraient du provoquer une erreur."
        )


def test_manual_market_data_provider_returns_snapshot():
    """Verifie que le mode manuel produit un snapshot normalise."""

    provider = ManualMarketDataProvider(
        spot=500.0,
        previous_price=495.0,
        volatility=0.20
    )

    snapshot = provider.get_market_snapshot(
        ticker="spy"
    )

    assert snapshot.ticker == "SPY"
    assert snapshot.last_price == 500.0
    assert snapshot.previous_price == 495.0
    assert snapshot.daily_return > 0
    assert snapshot.annualized_volatility == 0.20
    assert snapshot.source == "Manual Mode"


def test_csv_market_data_provider_returns_snapshot(tmp_path):
    """Verifie que le provider CSV charge des donnees locales."""

    csv_path = tmp_path / "market_data.csv"

    data = pd.DataFrame(
        {
            "Date": pd.date_range(
                start="2024-01-01",
                periods=5,
                freq="D"
            ),
            "Ticker": [
                "SPY",
                "SPY",
                "SPY",
                "SPY",
                "SPY"
            ],
            "Close": [
                100.0,
                101.0,
                103.0,
                102.0,
                104.0
            ],
        }
    )

    data.to_csv(
        csv_path,
        index=False
    )

    provider = CsvMarketDataProvider(
        csv_path=csv_path
    )

    snapshot = provider.get_market_snapshot(
        ticker="SPY"
    )

    assert snapshot.last_price == 104.0
    assert snapshot.previous_price == 102.0
    assert snapshot.number_of_observations == 5
    assert snapshot.source == "CSV Provider"


def test_get_provider_returns_expected_provider(tmp_path):
    """Verifie la factory de providers."""

    csv_path = tmp_path / "market_data.csv"
    csv_path.write_text(
        "Date,Ticker,Close\n2024-01-01,SPY,100\n",
        encoding="utf-8"
    )

    manual_provider = get_provider(
        "Manuel",
        spot=500,
        volatility=0.2
    )
    csv_provider = get_provider(
        "CSV local",
        csv_path=csv_path
    )

    assert isinstance(
        manual_provider,
        ManualMarketDataProvider
    )
    assert isinstance(
        csv_provider,
        CsvMarketDataProvider
    )


def test_bloomberg_provider_is_optional():
    """Verifie que Bloomberg echoue proprement sans blpapi."""

    provider = BloombergProvider()

    try:
        provider.get_market_snapshot(
            ticker="SPY US Equity"
        )

    except ImportError as error:
        assert "BloombergProvider" in str(error)

    except NotImplementedError:
        assert True
