
"""
ARIA - Sauvegarde et lecture de l'historique des risques
"""

import csv
from datetime import datetime
from pathlib import Path

from anomaly_detector import RiskSnapshot


CSV_COLUMNS = [
    "timestamp",
    "spot",
    "implied_volatility",
    "portfolio_value",
    "delta",
    "gamma",
    "theta",
    "vega",
    "rho"
]


class RiskHistory:
    """Gère l'historique des snapshots dans un fichier CSV."""

    def __init__(
        self,
        file_path: str = "data/risk_history.csv"
    ) -> None:
        self.file_path = Path(file_path)

        # Crée automatiquement le dossier data s'il n'existe pas
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    def save_snapshot(
        self,
        snapshot: RiskSnapshot
    ) -> None:
        """Ajoute un snapshot à la fin du fichier CSV."""

        file_exists = self.file_path.exists()

        with self.file_path.open(
            mode="a",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=CSV_COLUMNS
            )

            # On écrit les noms de colonnes seulement au début du fichier
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                "timestamp": snapshot.timestamp.isoformat(),
                "spot": snapshot.spot,
                "implied_volatility": snapshot.implied_volatility,
                "portfolio_value": snapshot.portfolio_value,
                "delta": snapshot.delta,
                "gamma": snapshot.gamma,
                "theta": snapshot.theta,
                "vega": snapshot.vega,
                "rho": snapshot.rho
            })

    def save_snapshots(
        self,
        snapshots: list[RiskSnapshot]
    ) -> None:
        """Sauvegarde plusieurs snapshots."""

        for snapshot in snapshots:
            self.save_snapshot(snapshot)

    def load_snapshots(self) -> list[RiskSnapshot]:
        """Lit le fichier CSV et recrée les snapshots."""

        if not self.file_path.exists():
            return []

        snapshots = []

        with self.file_path.open(
            mode="r",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            for row in reader:
                snapshot = RiskSnapshot(
                    timestamp=datetime.fromisoformat(
                        row["timestamp"]
                    ),
                    spot=float(row["spot"]),
                    implied_volatility=float(
                        row["implied_volatility"]
                    ),
                    portfolio_value=float(
                        row["portfolio_value"]
                    ),
                    delta=float(row["delta"]),
                    gamma=float(row["gamma"]),
                    theta=float(row["theta"]),
                    vega=float(row["vega"]),
                    rho=float(row["rho"])
                )

                snapshots.append(snapshot)

        return snapshots

    def get_last_snapshot(
        self
    ) -> RiskSnapshot | None:
        """Renvoie le snapshot le plus récent."""

        snapshots = self.load_snapshots()

        if not snapshots:
            return None

        return snapshots[-1]

    def clear_history(self) -> None:
        """Supprime le fichier d'historique."""

        if self.file_path.exists():
            self.file_path.unlink()


if __name__ == "__main__":
    history = RiskHistory()

    # On efface l'ancien fichier pour cette démonstration
    history.clear_history()

    first_snapshot = RiskSnapshot(
        timestamp=datetime.now(),
        spot=500,
        implied_volatility=0.20,
        portfolio_value=1000,
        delta=5.0,
        gamma=0.20,
        theta=-1.0,
        vega=10.0,
        rho=1.0
    )

    second_snapshot = RiskSnapshot(
        timestamp=datetime.now(),
        spot=490,
        implied_volatility=0.24,
        portfolio_value=950,
        delta=6.5,
        gamma=0.25,
        theta=-1.2,
        vega=12.0,
        rho=1.1
    )

    history.save_snapshot(first_snapshot)
    history.save_snapshot(second_snapshot)

    saved_snapshots = history.load_snapshots()

    print("Historique ARIA")
    print(
        f"{len(saved_snapshots)} snapshot(s) enregistré(s)."
    )

    for snapshot in saved_snapshots:
        print(
            f"\nDate : {snapshot.timestamp}"
            f"\nSpot : {snapshot.spot}"
            f"\nVolatilité : {snapshot.implied_volatility:.2%}"
            f"\nValeur du portefeuille : {snapshot.portfolio_value:.2f}"
            f"\nDelta : {snapshot.delta:.4f}"
            f"\nVega : {snapshot.vega:.4f}"
        )

    last_snapshot = history.get_last_snapshot()

    if last_snapshot is not None:
        print(
            "\nDernier spot enregistré : "
            f"{last_snapshot.spot}"
        )

