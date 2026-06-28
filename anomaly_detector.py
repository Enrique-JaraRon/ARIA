"""
ARIA - Détection simple d'anomalies de marché et de portefeuille
"""

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, pstdev

from portfolio import Portfolio
from pricing_BS import OptionContract


@dataclass
class RiskSnapshot:
    """
    Représente l'état du marché et du portefeuille à un instant donné.
    """

    timestamp: datetime
    spot: float
    implied_volatility: float
    portfolio_value: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError("Le spot doit être strictement positif.")

        if self.implied_volatility <= 0:
            raise ValueError(
                "La volatilité implicite doit être strictement positive."
            )


@dataclass
class Alert:
    """Représente une anomalie détectée."""

    name: str
    severity: str
    message: str
    current_value: float
    reference_value: float | None = None
    z_score: float | None = None

    def display(self) -> None:
        print(f"\n[{self.severity}] {self.name}")
        print(self.message)
        print(f"Valeur actuelle : {self.current_value:.6f}")

        if self.reference_value is not None:
            print(
                f"Valeur de référence : "
                f"{self.reference_value:.6f}"
            )

        if self.z_score is not None:
            print(f"Z-score : {self.z_score:.2f}")


class AnomalyDetector:
    """
    Détecte des situations inhabituelles à partir de règles simples
    et de l'historique.
    """

    def __init__(
        self,
        delta_limit: float = 10.0,
        gamma_limit: float = 1.0,
        vega_limit: float = 20.0,
        daily_spot_move_limit: float = 0.03,
        volatility_move_limit: float = 0.05,
        z_score_limit: float = 2.5
    ) -> None:

        self.delta_limit = delta_limit
        self.gamma_limit = gamma_limit
        self.vega_limit = vega_limit
        self.daily_spot_move_limit = daily_spot_move_limit
        self.volatility_move_limit = volatility_move_limit
        self.z_score_limit = z_score_limit

    def calculate_z_score(
        self,
        current_value: float,
        historical_values: list[float]
    ) -> float | None:
        """
        Mesure à quel point une valeur est éloignée
        de son comportement historique moyen.
        """

        if len(historical_values) < 2:
            return None

        historical_mean = mean(historical_values)
        historical_std = pstdev(historical_values)

        if historical_std == 0:
            return None

        return (
            current_value - historical_mean
        ) / historical_std

    def severity_from_z_score(self, z_score: float) -> str:
        """Transforme un z-score en niveau de gravité."""

        absolute_z_score = abs(z_score)

        if absolute_z_score >= 4:
            return "CRITIQUE"

        if absolute_z_score >= 3:
            return "ÉLEVÉE"

        return "MODÉRÉE"

    def detect_exposure_limits(
        self,
        snapshot: RiskSnapshot
    ) -> list[Alert]:
        """Vérifie si certains Greeks dépassent les limites choisies."""

        alerts = []

        if abs(snapshot.delta) > self.delta_limit:
            alerts.append(
                Alert(
                    name="Exposition delta élevée",
                    severity="ÉLEVÉE",
                    message=(
                        "Le portefeuille est très sensible "
                        "aux mouvements du sous-jacent."
                    ),
                    current_value=snapshot.delta,
                    reference_value=self.delta_limit
                )
            )

        if abs(snapshot.gamma) > self.gamma_limit:
            alerts.append(
                Alert(
                    name="Exposition gamma élevée",
                    severity="ÉLEVÉE",
                    message=(
                        "Le delta du portefeuille peut changer rapidement "
                        "si le sous-jacent bouge."
                    ),
                    current_value=snapshot.gamma,
                    reference_value=self.gamma_limit
                )
            )

        if abs(snapshot.vega) > self.vega_limit:
            alerts.append(
                Alert(
                    name="Exposition vega élevée",
                    severity="ÉLEVÉE",
                    message=(
                        "Le portefeuille est très sensible "
                        "aux variations de volatilité implicite."
                    ),
                    current_value=snapshot.vega,
                    reference_value=self.vega_limit
                )
            )

        return alerts

    def detect_market_moves(
        self,
        current: RiskSnapshot,
        previous: RiskSnapshot
    ) -> list[Alert]:
        """Compare l'état actuel avec l'état précédent."""

        alerts = []

        spot_return = (
            current.spot - previous.spot
        ) / previous.spot

        volatility_change = (
            current.implied_volatility
            - previous.implied_volatility
        )

        if abs(spot_return) > self.daily_spot_move_limit:
            severity = (
                "CRITIQUE"
                if abs(spot_return) >= 0.05
                else "ÉLEVÉE"
            )

            alerts.append(
                Alert(
                    name="Mouvement important du sous-jacent",
                    severity=severity,
                    message=(
                        "Le sous-jacent a fortement bougé "
                        "par rapport à l'observation précédente."
                    ),
                    current_value=spot_return,
                    reference_value=self.daily_spot_move_limit
                )
            )

        if abs(volatility_change) > self.volatility_move_limit:
            severity = (
                "CRITIQUE"
                if abs(volatility_change) >= 0.10
                else "ÉLEVÉE"
            )

            alerts.append(
                Alert(
                    name="Variation importante de volatilité",
                    severity=severity,
                    message=(
                        "La volatilité implicite s'est fortement déplacée."
                    ),
                    current_value=volatility_change,
                    reference_value=self.volatility_move_limit
                )
            )

        return alerts

    def detect_historical_anomalies(
        self,
        current: RiskSnapshot,
        history: list[RiskSnapshot]
    ) -> list[Alert]:
        """Compare les valeurs actuelles à leur historique."""

        alerts = []

        fields_to_check = {
            "delta": "Delta inhabituel",
            "gamma": "Gamma inhabituel",
            "vega": "Vega inhabituel",
            "implied_volatility": "Volatilité implicite inhabituelle"
        }

        for field_name, alert_name in fields_to_check.items():
            current_value = getattr(current, field_name)

            historical_values = [
                getattr(snapshot, field_name)
                for snapshot in history
            ]

            z_score = self.calculate_z_score(
                current_value=current_value,
                historical_values=historical_values
            )

            if z_score is None:
                continue

            if abs(z_score) >= self.z_score_limit:
                alerts.append(
                    Alert(
                        name=alert_name,
                        severity=self.severity_from_z_score(
                            z_score
                        ),
                        message=(
                            "La valeur actuelle est très éloignée "
                            "de son comportement historique."
                        ),
                        current_value=current_value,
                        reference_value=mean(
                            historical_values
                        ),
                        z_score=z_score
                    )
                )

        return alerts

    def detect_all(
        self,
        current: RiskSnapshot,
        history: list[RiskSnapshot] | None = None,
        previous: RiskSnapshot | None = None
    ) -> list[Alert]:
        """Lance toutes les méthodes de détection disponibles."""

        alerts = []

        alerts.extend(
            self.detect_exposure_limits(current)
        )

        if previous is not None:
            alerts.extend(
                self.detect_market_moves(
                    current=current,
                    previous=previous
                )
            )

        if history:
            alerts.extend(
                self.detect_historical_anomalies(
                    current=current,
                    history=history
                )
            )

        return alerts


def create_snapshot(
    portfolio: Portfolio,
    spot: float,
    implied_volatility: float
) -> RiskSnapshot:
    """Crée un snapshot à partir d'un portefeuille."""

    greeks = portfolio.total_greeks()

    return RiskSnapshot(
        timestamp=datetime.now(),
        spot=spot,
        implied_volatility=implied_volatility,
        portfolio_value=portfolio.total_market_value(),
        delta=greeks["delta"],
        gamma=greeks["gamma"],
        theta=greeks["theta"],
        vega=greeks["vega"],
        rho=greeks["rho"]
    )


if __name__ == "__main__":
    portfolio = Portfolio(
        name="Portefeuille ARIA"
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
        sigma=0.25,
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

    previous_snapshot = create_snapshot(
        portfolio=portfolio,
        spot=500,
        implied_volatility=0.20
    )

    history = [
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=495,
            implied_volatility=0.18,
            portfolio_value=1000,
            delta=12.0,
            gamma=0.05,
            theta=-2.0,
            vega=8.0,
            rho=1.0
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=500,
            implied_volatility=0.19,
            portfolio_value=1050,
            delta=12.5,
            gamma=0.06,
            theta=-2.1,
            vega=8.5,
            rho=1.1
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=502,
            implied_volatility=0.20,
            portfolio_value=1080,
            delta=11.8,
            gamma=0.05,
            theta=-2.2,
            vega=9.0,
            rho=1.0
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=498,
            implied_volatility=0.19,
            portfolio_value=1020,
            delta=12.2,
            gamma=0.06,
            theta=-2.0,
            vega=8.7,
            rho=1.2
        )
    ]

    current_snapshot = create_snapshot(
        portfolio=portfolio,
        spot=470,
        implied_volatility=0.32
    )

    detector = AnomalyDetector(
        delta_limit=10,
        gamma_limit=1,
        vega_limit=20,
        daily_spot_move_limit=0.03,
        volatility_move_limit=0.05,
        z_score_limit=2.5
    )

    alerts = detector.detect_all(
        current=current_snapshot,
        history=history,
        previous=previous_snapshot
    )

    print("ARIA - Détection d'anomalies")

    if not alerts:
        print("\nAucune anomalie détectée.")

    else:
        print(
            f"\n{len(alerts)} anomalie(s) détectée(s)."
        )

        for alert in alerts:
            alert.display()
