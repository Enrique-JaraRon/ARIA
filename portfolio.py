
"""
ARIA - Gestion d'un portefeuille d'options
"""

from dataclasses import dataclass, field
from typing import Literal

from pricing_BS import OptionContract, bs_price, bs_greeks


@dataclass
class OptionPosition:
    """Représente une position sur une option."""

    contract: OptionContract
    quantity: int
    name: str = ""

    def market_value(self) -> float:
        """
        Calcule la valeur totale de la position.

        Une quantité positive représente une position achetée.
        Une quantité négative représente une position vendue.
        """

        return bs_price(self.contract) * self.quantity

    def total_greeks(self) -> dict[str, float]:
        """Calcule les Greeks de toute la position."""

        greeks = bs_greeks(self.contract)

        return {
            "delta": greeks["delta"] * self.quantity,
            "gamma": greeks["gamma"] * self.quantity,
            "theta": greeks["theta"] * self.quantity,
            "vega": greeks["vega"] * self.quantity,
            "rho": greeks["rho"] * self.quantity,
            "vanna": greeks["vanna"] * self.quantity,
            "volga": greeks["volga"] * self.quantity,
        }


@dataclass
class StockPosition:
    """Représente une position sur le sous-jacent."""

    spot: float
    quantity: int
    name: str = "Sous-jacent"

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError(
                "Le prix du sous-jacent doit être strictement positif."
            )

    def market_value(self) -> float:
        """Calcule la valeur totale de la position en actions."""

        return self.spot * self.quantity

    def total_greeks(self) -> dict[str, float]:
        """
        Une action a un delta égal à 1.

        Les autres Greeks sont considérés comme nuls
        dans ce modèle simplifié.
        """

        return {
            "delta": float(self.quantity),
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
            "vanna": 0.0,
            "volga": 0.0,
        }


Position = OptionPosition | StockPosition


@dataclass
class Portfolio:
    """Regroupe plusieurs positions financières."""

    name: str = "Portefeuille ARIA"
    positions: list[Position] = field(default_factory=list)

    def add_option(
        self,
        contract: OptionContract,
        quantity: int,
        name: str = ""
    ) -> None:
        """Ajoute une position sur option."""

        if quantity == 0:
            raise ValueError(
                "La quantité ne peut pas être égale à zéro."
            )

        position = OptionPosition(
            contract=contract,
            quantity=quantity,
            name=name
        )

        self.positions.append(position)

    def add_stock(
        self,
        spot: float,
        quantity: int,
        name: str = "Sous-jacent"
    ) -> None:
        """Ajoute une position sur le sous-jacent."""

        if quantity == 0:
            raise ValueError(
                "La quantité ne peut pas être égale à zéro."
            )

        position = StockPosition(
            spot=spot,
            quantity=quantity,
            name=name
        )

        self.positions.append(position)

    def remove_position(self, index: int) -> None:
        """Supprime une position grâce à son numéro."""

        if index < 0 or index >= len(self.positions):
            raise IndexError(
                "Le numéro de position n'existe pas."
            )

        self.positions.pop(index)

    def total_market_value(self) -> float:
        """Calcule la valeur totale du portefeuille."""

        return sum(
            position.market_value()
            for position in self.positions
        )

    def total_greeks(self) -> dict[str, float]:
        """Additionne les Greeks de toutes les positions."""

        totals = {
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
            "vanna": 0.0,
            "volga": 0.0,
        }

        for position in self.positions:
            position_greeks = position.total_greeks()

            for greek in totals:
                totals[greek] += position_greeks[greek]

        return totals

    def summary(self) -> None:
        """Affiche un résumé lisible du portefeuille."""

        print(f"\n{self.name}")
        print(f"Nombre de positions : {len(self.positions)}")

        if not self.positions:
            print("Le portefeuille est vide.")
            return

        print("\nPositions")

        for index, position in enumerate(
            self.positions,
            start=1
        ):
            position_name = (
                position.name
                if position.name
                else f"Position {index}"
            )

            if isinstance(position, OptionPosition):
                contract = position.contract

                print(
                    f"{index}. {position_name} | "
                    f"{position.quantity:+d} "
                    f"{contract.option_type.upper()} | "
                    f"Strike {contract.K} | "
                    f"Maturité {contract.T} an | "
                    f"Valeur {position.market_value():.2f}"
                )

            else:
                print(
                    f"{index}. {position_name} | "
                    f"{position.quantity:+d} actions | "
                    f"Spot {position.spot} | "
                    f"Valeur {position.market_value():.2f}"
                )

        totals = self.total_greeks()

        print("\nValeur totale")
        print(f"{self.total_market_value():.2f}")

        print("\nGreeks du portefeuille")
        print(f"Delta : {totals['delta']:.6f}")
        print(f"Gamma : {totals['gamma']:.6f}")
        print(f"Theta : {totals['theta']:.6f}")
        print(f"Vega : {totals['vega']:.6f}")
        print(f"Rho : {totals['rho']:.6f}")
        print(f"Vanna : {totals['vanna']:.6f}")
        print(f"Volga : {totals['volga']:.6f}")


if __name__ == "__main__":
    portfolio = Portfolio(
        name="Portefeuille de démonstration"
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
        quantity=10,
        name="Calls ATM achetés"
    )

    portfolio.add_option(
        contract=put,
        quantity=-5,
        name="Puts vendus"
    )

    portfolio.add_stock(
        spot=500,
        quantity=-3,
        name="Couverture en SPY"
    )

    portfolio.summary()

