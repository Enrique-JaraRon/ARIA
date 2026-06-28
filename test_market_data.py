"""
Tests du module market_data.py
"""

import sys
import types

import pandas as pd

from market_data import get_market_snapshot


class FakeYFinance:
    """Fausse version de yfinance pour éviter un appel internet."""

    @staticmethod
    def download(
        ticker,
        period="6mo",
        progress=False,
        auto_adjust=True
    ):
        """Renvoie des données fictives de marché."""

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
    """Vérifie que le snapshot de marché est correctement calculé."""

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


def test_get_market_snapshot_rejects_empty_ticker():
    """Vérifie qu'un ticker vide est refusé."""

    try:
        get_market_snapshot(
            ticker=""
        )

    except ValueError as error:
        assert "ticker" in str(error).lower()

    else:
        raise AssertionError(
            "Un ticker vide aurait dû provoquer une erreur."
        )


def test_get_market_snapshot_rejects_empty_data(monkeypatch):
    """Vérifie qu'une réponse vide de Yahoo Finance est refusée."""

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
        assert "aucune donnée" in str(error).lower()

    else:
        raise AssertionError(
            "Des données vides auraient dû provoquer une erreur."
        )
