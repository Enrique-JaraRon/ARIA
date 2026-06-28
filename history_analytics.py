"""
ARIA - Analyse de l'historique des risques
"""

import pandas as pd


def load_history_dataframe(
    file_path: str = "data/risk_history.csv"
) -> pd.DataFrame:
    """Charge l'historique des snapshots dans un DataFrame."""

    try:
        history = pd.read_csv(
            file_path
        )

    except FileNotFoundError:
        return pd.DataFrame()

    if history.empty:
        return history

    if "timestamp" in history.columns:
        history["timestamp"] = pd.to_datetime(
            history["timestamp"],
            errors="coerce"
        )

        history = history.sort_values(
            "timestamp"
        )

    return history


def clean_history_dataframe(
    history: pd.DataFrame
) -> pd.DataFrame:
    """Nettoie l'historique pour l'affichage."""

    if history.empty:
        return history

    cleaned_history = history.copy()

    numeric_columns = [
        "spot",
        "implied_volatility",
        "portfolio_value",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "vanna",
        "volga"
    ]

    for column in numeric_columns:

        if column in cleaned_history.columns:
            cleaned_history[column] = pd.to_numeric(
                cleaned_history[column],
                errors="coerce"
            )

    return cleaned_history


def get_latest_snapshot(
    history: pd.DataFrame
) -> pd.Series | None:
    """Renvoie le dernier snapshot disponible."""

    if history.empty:
        return None

    return history.iloc[-1]


def get_history_summary(
    history: pd.DataFrame
) -> dict[str, float | int | None]:
    """Calcule quelques statistiques simples sur l'historique."""

    if history.empty:
        return {
            "number_of_snapshots": 0,
            "latest_portfolio_value": None,
            "latest_spot": None,
            "latest_volatility": None,
            "minimum_portfolio_value": None,
            "maximum_portfolio_value": None
        }

    latest_snapshot = get_latest_snapshot(
        history
    )

    summary = {
        "number_of_snapshots": len(history),
        "latest_portfolio_value": None,
        "latest_spot": None,
        "latest_volatility": None,
        "minimum_portfolio_value": None,
        "maximum_portfolio_value": None
    }

    if latest_snapshot is not None:

        if "portfolio_value" in history.columns:
            summary["latest_portfolio_value"] = (
                latest_snapshot["portfolio_value"]
            )

            summary["minimum_portfolio_value"] = (
                history["portfolio_value"].min()
            )

            summary["maximum_portfolio_value"] = (
                history["portfolio_value"].max()
            )

        if "spot" in history.columns:
            summary["latest_spot"] = (
                latest_snapshot["spot"]
            )

        if "implied_volatility" in history.columns:
            summary["latest_volatility"] = (
                latest_snapshot["implied_volatility"]
            )

    return summary


if __name__ == "__main__":

    history_data = load_history_dataframe(
        "data/risk_history.csv"
    )

    history_data = clean_history_dataframe(
        history_data
    )

    summary = get_history_summary(
        history_data
    )

    print("Historique ARIA")
    print(history_data)

    print("\nRésumé")
    print(summary)
