# ARIA - Streamlit Cloud Deployment

## App settings

- Repository: `https://github.com/Enrique-JaraRon/ARIA`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: choose the same version used locally when possible. ARIA is tested locally with Python 3.13 and supports Python 3.11+.

## Secrets

Do not commit `.env` or `.streamlit/secrets.toml`.

In Streamlit Cloud, open the app settings, then add these secrets:

```toml
OPENAI_API_KEY = "sk-..."
ARIA_LLM_MODEL = "gpt-5-mini"
```

ARIA reads configuration in this order:

1. Streamlit Cloud secrets through `st.secrets`.
2. Local `.env` / environment variables.

This keeps local development and cloud deployment compatible.

## Local run

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8502
```

## Streamlit Cloud run

1. Push the latest `main` branch to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from the existing GitHub repo.
4. Select repository `Enrique-JaraRon/ARIA`.
5. Select branch `main`.
6. Set main file path to `streamlit_app.py`.
7. Open Advanced settings and choose the desired Python version.
8. Add the secrets above.
9. Deploy.

## Runtime files

At startup, ARIA creates these folders if missing:

- `data/`
- `data/portfolios/`
- `tmp/`

Generated local files such as `data/risk_history.csv`, `.env`,
`.streamlit/secrets.toml`, and `tmp/*.log` are ignored by Git.
