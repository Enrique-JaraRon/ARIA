# ARIA - Adaptive Risk Intelligence Agent

ARIA est une application Python / Streamlit de gestion des risques financiers.

Le projet permet de construire un portefeuille composé d'options et d'actions, de calculer sa valeur, ses Greeks, ses stress tests, sa VaR, son Expected Shortfall, son score de risque global, puis de générer une analyse explicative avec un LLM.

## Objectif du projet

L'objectif d'ARIA est de simuler un mini outil de risk management utilisé en salle de marché.

Le projet combine :

- pricing Black-Scholes ;
- gestion d'un portefeuille multi-positions ;
- calcul des Greeks ;
- stress tests ;
- matrice de risque spot / volatilité ;
- profil de P&L ;
- profil des Greeks ;
- VaR et Expected Shortfall ;
- scoring de risque ;
- détection d'anomalies ;
- explication automatique par LLM ;
- connexion optionnelle à des données de marché via Yahoo Finance.

## Fonctionnalités principales

### Pricing d'options

ARIA utilise le modèle de Black-Scholes pour valoriser des options européennes call et put.

Le module calcule aussi les principaux Greeks :

- Delta ;
- Gamma ;
- Theta ;
- Vega ;
- Rho ;
- Vanna ;
- Volga.

### Portefeuille

L'utilisateur peut construire un portefeuille avec :

- options call ;
- options put ;
- positions longues ou courtes ;
- actions ;
- multiplicateur de contrat.

Une quantité positive représente une position achetée.

Une quantité négative représente une position vendue.

### Stress tests

ARIA applique plusieurs scénarios de marché au portefeuille :

- baisse du spot ;
- hausse du spot ;
- choc de volatilité ;
- scénario personnalisé.

Chaque scénario calcule :

- valeur initiale ;
- valeur stressée ;
- profit ou perte ;
- Greeks stressés.

### Matrice de risque

ARIA affiche une matrice croisant plusieurs variations de spot et de volatilité.

Elle permet de voir rapidement les zones favorables et défavorables du portefeuille.

### Profil de P&L

ARIA calcule le profit ou la perte du portefeuille pour plusieurs niveaux du sous-jacent.

L'application affiche aussi le point mort estimé du portefeuille.

### Profil des Greeks

ARIA montre comment les Greeks évoluent lorsque le sous-jacent monte ou baisse.

Cela permet de visualiser les risques non linéaires du portefeuille.

### Couverture delta indicative

ARIA calcule la quantité de sous-jacent nécessaire pour rendre le portefeuille approximativement delta-neutre.

Cette couverture est indicative : elle neutralise le delta instantané, mais pas le gamma, la vega ou les autres risques.

### VaR et Expected Shortfall

ARIA réalise une simulation Monte Carlo simplifiée pour estimer :

- la VaR ;
- l'Expected Shortfall ;
- la pire perte simulée ;
- la distribution des pertes.

Une VaR paramétrique simplifiée est aussi calculée à partir du delta.

### Risk Score ARIA

ARIA produit un score de risque global entre 0 et 100.

Le score combine :

- dépassements de limites de Greeks ;
- alertes quantitatives ;
- VaR ;
- Expected Shortfall ;
- pire stress test.

Les niveaux sont :

- 0 à 30 : risque faible ;
- 30 à 60 : risque modéré ;
- 60 à 80 : risque élevé ;
- 80 à 100 : risque critique.

### Historique

ARIA sauvegarde les snapshots de risque dans un fichier CSV.

L'application permet ensuite de visualiser l'évolution historique de plusieurs métriques :

- valeur du portefeuille ;
- spot ;
- volatilité ;
- Delta ;
- Gamma ;
- Theta ;
- Vega ;
- Rho ;
- Vanna ;
- Volga.

### Données de marché

ARIA peut fonctionner en mode manuel ou en mode connecté à Yahoo Finance.

En mode Yahoo Finance, l'application récupère :

- le dernier prix du sous-jacent ;
- le rendement journalier ;
- la volatilité historique annualisée.

Cette volatilité peut ensuite être utilisée pour les calculs de risque.

### Analyse LLM

Lorsqu'une anomalie est détectée, ARIA peut demander à un LLM de générer une explication en langage naturel.

Le LLM ne fait pas les calculs de risque.

Il sert uniquement à interpréter les résultats produits par les modules quantitatifs.

## Structure du projet

```text
ARIA/
│
├── streamlit_app.py
│
├── pricing_BS.py
├── portfolio.py
├── scenario_analysis.py
├── risk_surface.py
├── pnl_profile.py
├── greeks_profile.py
├── var_analysis.py
├── risk_score.py
├── hedging_analysis.py
├── anomaly_detector.py
├── risk_history.py
├── history_analytics.py
├── market_data.py
├── llm_explainer.py
├── aria_workflow.py
│
├── test_pricing.py
├── test_portfolio.py
├── test_anomaly_detector.py
├── test_risk_history.py
│
├── requirements.txt
├── .gitignore
└── data/
    └── risk_history.csv