"""
ARIA - Explication des alertes avec un LLM
"""

import os

from openai import OpenAI

from anomaly_detector import Alert, RiskSnapshot


class LLMExplainer:
    """Transforme les alertes quantitatives en explication lisible."""

    def __init__(self, model: str) -> None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "La variable OPENAI_API_KEY n'est pas définie."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def build_prompt(
        self,
        snapshot: RiskSnapshot,
        alerts: list[Alert]
    ) -> str:
        """Prépare les informations envoyées au LLM."""

        alert_lines = []

        for alert in alerts:
            line = (
                f"- {alert.name} | "
                f"gravité : {alert.severity} | "
                f"valeur actuelle : {alert.current_value:.6f}"
            )

            if alert.reference_value is not None:
                line += (
                    f" | référence : "
                    f"{alert.reference_value:.6f}"
                )

            if alert.z_score is not None:
                line += f" | z-score : {alert.z_score:.2f}"

            alert_lines.append(line)

        if alert_lines:
            alerts_text = "\n".join(alert_lines)

        else:
            alerts_text = (
                "Aucune alerte quantitative n'a ete detectee par ARIA."
            )

        return f"""
Tu es l'assistant d'analyse des risques d'ARIA.

Tu reçois uniquement des résultats déjà calculés par un moteur quantitatif.
Tu ne dois pas inventer de données ni prétendre prédire le marché.
Tu ne dois pas donner de conseil financier personnalisé.
Tu dois rester prudent et rappeler que l'analyse dépend des hypothèses du modèle.

État actuel :
- Spot : {snapshot.spot}
- Volatilité implicite : {snapshot.implied_volatility:.2%}
- Valeur du portefeuille : {snapshot.portfolio_value:.2f}
- Delta : {snapshot.delta:.6f}
- Gamma : {snapshot.gamma:.6f}
- Theta : {snapshot.theta:.6f}
- Vega : {snapshot.vega:.6f}
- Rho : {snapshot.rho:.6f}

Alertes détectées :
{alerts_text}

Réponds en français avec cette structure :

1. Résumé exécutif
2. Niveau de risque global
3. Principaux facteurs de risque
4. Lecture des Greeks
5. Lecture des stress tests si les données sont disponibles
6. Lecture VaR / Expected Shortfall si les données sont disponibles
7. Couverture et actions possibles à étudier
8. Points à surveiller
9. Limites du modèle

Si une information numérique n'est pas fournie, indique qu'elle n'est pas disponible.
Précise que les couvertures proposées doivent être vérifiées avant toute décision.
""".strip()

    def explain(
        self,
        snapshot: RiskSnapshot,
        alerts: list[Alert]
    ) -> str:
        """Envoie les alertes au LLM et récupère son explication."""

        prompt = self.build_prompt(
            snapshot=snapshot,
            alerts=alerts
        )

        response = self.client.responses.create(
            model=self.model,
            input=prompt
        )

        return response.output_text


if __name__ == "__main__":
    from datetime import datetime

    snapshot = RiskSnapshot(
        timestamp=datetime.now(),
        spot=465,
        implied_volatility=0.32,
        portfolio_value=850,
        delta=18.0,
        gamma=1.4,
        theta=-4.0,
        vega=30.0,
        rho=2.0
    )

    alerts = [
        Alert(
            name="Exposition delta élevée",
            severity="ÉLEVÉE",
            message=(
                "Le portefeuille est très sensible "
                "aux mouvements du sous-jacent."
            ),
            current_value=18.0,
            reference_value=10.0
        ),
        Alert(
            name="Variation importante de volatilité",
            severity="CRITIQUE",
            message=(
                "La volatilité implicite a fortement augmenté."
            ),
            current_value=0.12,
            reference_value=0.05,
            z_score=3.8
        )
    ]

    model = os.getenv("ARIA_LLM_MODEL")

    if not model:
        raise ValueError(
            "La variable ARIA_LLM_MODEL n'est pas définie."
        )

    explainer = LLMExplainer(model=model)

    explanation = explainer.explain(
        snapshot=snapshot,
        alerts=alerts
    )

    print("Analyse ARIA\n")
    print(explanation)


