"""
ARIA - Diagnostic du projet
"""

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REQUIRED_FILES = [
    "streamlit_app.py",
    "portfolio_engine/pricing_BS.py",
    "portfolio_engine/portfolio.py",
    "portfolio_engine/demo_portfolios.py",
    "portfolio_engine/portfolio_analytics.py",
    "risk_engine/scenario_analysis.py",
    "risk_engine/risk_surface.py",
    "risk_engine/pnl_profile.py",
    "risk_engine/greeks_profile.py",
    "risk_engine/var_analysis.py",
    "risk_engine/risk_score.py",
    "risk_engine/hedging_analysis.py",
    "risk_engine/anomaly_detector.py",
    "risk_engine/risk_history.py",
    "risk_engine/history_analytics.py",
    "portfolio_engine/market_data.py",
    "app/ui_components.py",
    "app/report_generator.py",
    "app/llm_explainer.py",
    "app/app_config.py",
    "app/aria_workflow.py",
    "tools/quality_check.py",
    "scripts/run_aria.py",
    "scripts/start_aria.bat",
    "scripts/check_quality.bat",
    ".env.example",
    "requirements.txt",
    "README.md",
    ".gitignore",
    "tests/test_ui_components.py",
    "tests/test_demo_portfolios.py",
    "tests/test_quantitative_consistency.py",
    "docs/screenshots/.gitkeep",
    "screenshots/.gitkeep",
]

REQUIRED_MODULES = [
    "streamlit",
    "pandas",
    "numpy",
    "scipy",
    "altair",
    "reportlab",
    "openai",
    "dotenv",
    "pytest",
    "yfinance"
]


PROJECT_MODULES = [
    "portfolio_engine.pricing_BS",
    "portfolio_engine.portfolio",
    "portfolio_engine.demo_portfolios",
    "portfolio_engine.portfolio_analytics",
    "portfolio_engine.market_data",
    "risk_engine.scenario_analysis",
    "risk_engine.risk_surface",
    "risk_engine.pnl_profile",
    "risk_engine.greeks_profile",
    "risk_engine.var_analysis",
    "risk_engine.risk_score",
    "risk_engine.hedging_analysis",
    "risk_engine.anomaly_detector",
    "risk_engine.risk_history",
    "risk_engine.history_analytics",
    "risk_engine.probabilistic_risk",
    "app.ui_components",
    "app.report_generator",
    "app.llm_explainer",
    "app.app_config",
    "app.aria_workflow",
]


def check_required_files(
    project_path: Path
) -> list[str]:
    """Vérifie que les fichiers importants existent."""

    messages = []

    for file_name in REQUIRED_FILES:

        file_path = project_path / file_name

        if file_path.exists():
            messages.append(
                f"OK fichier trouvé : {file_name}"
            )

        else:
            messages.append(
                f"MANQUANT fichier absent : {file_name}"
            )

    return messages


def check_data_folder(
    project_path: Path
) -> list[str]:
    """Vérifie que le dossier data existe."""

    messages = []

    data_path = project_path / "data"

    if data_path.exists() and data_path.is_dir():
        messages.append(
            "OK dossier data trouvé"
        )

    else:
        messages.append(
            "MANQUANT dossier data absent"
        )

    history_file = data_path / "risk_history.csv"

    if history_file.exists():
        messages.append(
            "OK historique trouvé : data/risk_history.csv"
        )

    else:
        messages.append(
            "INFO aucun historique trouvé pour le moment"
        )

    return messages


def check_python_dependencies() -> list[str]:
    """Vérifie que les librairies externes sont installées."""

    messages = []

    for module_name in REQUIRED_MODULES:

        try:
            importlib.import_module(
                module_name
            )

            messages.append(
                f"OK dépendance installée : {module_name}"
            )

        except ImportError:
            messages.append(
                f"MANQUANT dépendance absente : {module_name}"
            )

    return messages


def check_project_modules() -> list[str]:
    """Vérifie que les modules internes ARIA sont importables."""

    messages = []

    for module_name in PROJECT_MODULES:

        try:
            importlib.import_module(
                module_name
            )

            messages.append(
                f"OK module ARIA importable : {module_name}"
            )

        except Exception as error:
            messages.append(
                f"ERREUR module ARIA : {module_name} -> {error}"
            )

    return messages


def check_environment_variables(
    project_path: Path
) -> list[str]:
    """Vérifie la configuration du fichier .env."""

    from app.app_config import get_runtime_setting

    messages = []

    env_path = project_path / ".env"

    if env_path.exists():
        messages.append(
            "OK fichier .env trouvé"
        )

    else:
        messages.append(
            "INFO fichier .env absent"
        )

    gitignore_path = project_path / ".gitignore"
    gitignore_text = (
        gitignore_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
        if gitignore_path.exists()
        else ""
    )

    if ".env" in gitignore_text:
        messages.append(
            "OK .env est ignore par Git"
        )
    else:
        messages.append(
            "ERREUR .env n'est pas ignore par Git"
        )

    if ".streamlit/secrets.toml" in gitignore_text:
        messages.append(
            "OK .streamlit/secrets.toml est ignore par Git"
        )
    else:
        messages.append(
            "ERREUR .streamlit/secrets.toml n'est pas ignore par Git"
        )

    openai_key = get_runtime_setting(
        "OPENAI_API_KEY"
    )

    llm_model = get_runtime_setting(
        "ARIA_LLM_MODEL"
    )

    if openai_key:
        messages.append(
            "OK variable OPENAI_API_KEY configurée"
        )

    else:
        messages.append(
            "INFO variable OPENAI_API_KEY non configurée"
        )

    if llm_model:
        messages.append(
            f"OK variable ARIA_LLM_MODEL configurée : {llm_model}"
        )

    else:
        messages.append(
            "INFO variable ARIA_LLM_MODEL non configurée"
        )

    return messages


def print_section(
    title: str,
    messages: list[str]
) -> None:
    """Affiche une section de diagnostic."""

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    for message in messages:
        print(message)


def run_diagnostics() -> None:
    """Lance tous les diagnostics du projet."""

    project_path = PROJECT_ROOT

    print()
    print("Diagnostic ARIA")
    print(f"Dossier analysé : {project_path}")

    print_section(
        "Fichiers du projet",
        check_required_files(
            project_path
        )
    )

    print_section(
        "Dossier data",
        check_data_folder(
            project_path
        )
    )

    print_section(
        "Dépendances Python",
        check_python_dependencies()
    )

    print_section(
        "Modules ARIA",
        check_project_modules()
    )

    print_section(
        "Variables d'environnement",
        check_environment_variables(
            project_path
        )
    )

    print()
    print("=" * 70)
    print("Diagnostic terminé")
    print("=" * 70)


if __name__ == "__main__":
    run_diagnostics()
