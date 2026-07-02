"""
ARIA - Script de lancement de l'application Streamlit
"""

import os
import socket
import subprocess
import sys
from pathlib import Path


def get_local_ip() -> str:
    """Return the best local IPv4 address for phone demos."""

    try:
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        ) as connection:
            connection.connect(
                (
                    "8.8.8.8",
                    80
                )
            )
            return connection.getsockname()[0]

    except OSError:
        return "127.0.0.1"


def main() -> int:
    """Lance l'application Streamlit ARIA."""

    project_path = Path(__file__).resolve().parents[1]
    app_path = project_path / "streamlit_app.py"
    port = os.getenv(
        "ARIA_STREAMLIT_PORT",
        "8502"
    )
    address = os.getenv(
        "ARIA_STREAMLIT_ADDRESS",
        "0.0.0.0"
    )
    local_ip = get_local_ip()

    if not app_path.exists():
        print("ERREUR : streamlit_app.py est introuvable.")
        print(f"Dossier analysé : {project_path}")
        return 1

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        address,
        "--server.port",
        port,
        "--server.headless",
        "true",
    ]

    print()
    print("=" * 80)
    print("Lancement de ARIA")
    print("=" * 80)
    print("Commande :")
    print(" ".join(command))
    print()
    print("Ordinateur :")
    print(f"  http://localhost:{port}")
    print("Telephone sur le meme Wi-Fi :")
    print(f"  http://{local_ip}:{port}")
    print()
    print("API LLM : configure OPENAI_API_KEY dans .env puis active le LLM dans la sidebar.")
    print()

    completed_process = subprocess.run(
        command,
        check=False,
    )

    return completed_process.returncode


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
