# ARIA - Adaptive Risk Intelligence Agent

ARIA est une application Streamlit de risk management pour portefeuille actions,
ETF et options. Elle est pensée pour une démonstration claire en entretien :
composition du portefeuille, validation, stress tests, VaR, Greeks, risque
probabiliste, alertes et rapport téléchargeable.

Projet développé par **Enrique Jara Ron**.

> Prototype éducatif. Les résultats ne sont pas un conseil financier et ne
> garantissent pas une performance future.

## Fonctionnalités

- Portefeuille client modifiable avec contrôles de cohérence.
- Portefeuilles de démonstration simples et utiles.
- Pricing Black-Scholes, Greeks et sensibilités au spot.
- Stress tests, matrice spot / volatilité, VaR et Expected Shortfall.
- Analyse probabiliste Monte Carlo avec contributeurs de pertes extrêmes.
- Alertes quantitatives et commentaire LLM optionnel.
- Rapport Markdown, PDF français et PDF anglais.
- Interface en français avec bouton de bascule en anglais.

## Captures de l'application

### Portefeuille client

![Portefeuille client](screenshots/portfolio_editor.png)

### Score de risque

![Score ARIA](screenshots/dashboard.png)

### Stress tests

![Stress tests](screenshots/stress_testing.png)

### Matrice rouge / vert

![Matrice de stress](screenshots/risk_matrix.png)

### VaR et Expected Shortfall

![VaR](screenshots/var_analysis.png)

### Sensibilités P&L

![Sensibilités P&L](screenshots/sensitivities_pnl.png)

### Evolution des Greeks

![Greeks](screenshots/greeks_profile.png)

### Risque probabiliste

![Risque probabiliste](screenshots/probabilistic_risk.png)

### Alertes et rapport

![Rapport](screenshots/risk_report.png)

### Mode anglais

![Mode anglais](screenshots/english_mode.png)

## Portefeuilles de démonstration

- `Conservative Balanced Portfolio`
- `Global Diversified Portfolio`
- `Tech Growth Portfolio`
- `Low Risk Options Portfolio`

## Structure

```text
app/                Interface, configuration, LLM et reporting
portfolio_engine/   Portefeuilles, instruments, pricing Black-Scholes
risk_engine/        Stress tests, VaR, Greeks, probabilités et score
tests/              Tests unitaires et contrôles quantitatifs
tools/              Diagnostic et contrôle qualité
scripts/            Scripts de lancement local
screenshots/        Captures utilisées dans ce README
```

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Lancement local

```powershell
streamlit run streamlit_app.py
```

Ou sur le port utilisé en démonstration :

```powershell
streamlit run streamlit_app.py --server.port 8502
```

Mode anglais direct :

```text
http://localhost:8502/?lang=en
```

## API / LLM

Le LLM est optionnel. Sans clé API, ARIA reste utilisable pour toute l'analyse
quantitative.

Créer un fichier `.env` local à partir de `.env.example` :

```powershell
Copy-Item .env.example .env
```

Exemple :

```text
OPENAI_API_KEY=sk-...
ARIA_LLM_MODEL=gpt-5-mini
```

## Streamlit Cloud

- Repository : `Enrique-JaraRon/ARIA`
- Branch : `main`
- Main file path : `streamlit_app.py`

Secrets optionnels :

```toml
OPENAI_API_KEY = "sk-..."
ARIA_LLM_MODEL = "gpt-5-mini"
```

## Qualité

```powershell
.\.venv\Scripts\python.exe tools\quality_check.py
```
