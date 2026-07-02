from datetime import datetime

import pytest

from risk_engine.anomaly_detector import RiskSnapshot
from risk_engine.risk_history import RiskHistory


@pytest.fixture
def snapshot():
    """Crée un snapshot simple utilisé dans plusieurs tests."""

    return RiskSnapshot(
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


def test_history_file_is_created(tmp_path, snapshot):
    """Vérifie que le fichier CSV est créé après une sauvegarde."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    history.save_snapshot(snapshot)

    assert file_path.exists()


def test_save_and_load_snapshot(tmp_path, snapshot):
    """Vérifie qu'un snapshot sauvegardé peut être relu."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    history.save_snapshot(snapshot)

    loaded_snapshots = history.load_snapshots()

    assert len(loaded_snapshots) == 1

    loaded_snapshot = loaded_snapshots[0]

    assert loaded_snapshot.spot == pytest.approx(500)
    assert loaded_snapshot.implied_volatility == pytest.approx(0.20)
    assert loaded_snapshot.portfolio_value == pytest.approx(1000)
    assert loaded_snapshot.delta == pytest.approx(5.0)
    assert loaded_snapshot.gamma == pytest.approx(0.20)
    assert loaded_snapshot.theta == pytest.approx(-1.0)
    assert loaded_snapshot.vega == pytest.approx(10.0)
    assert loaded_snapshot.rho == pytest.approx(1.0)


def test_save_multiple_snapshots(tmp_path):
    """Vérifie que plusieurs snapshots sont bien enregistrés."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

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
        spot=480,
        implied_volatility=0.28,
        portfolio_value=900,
        delta=8.0,
        gamma=0.35,
        theta=-1.5,
        vega=15.0,
        rho=1.2
    )

    history.save_snapshots(
        [first_snapshot, second_snapshot]
    )

    loaded_snapshots = history.load_snapshots()

    assert len(loaded_snapshots) == 2
    assert loaded_snapshots[0].spot == pytest.approx(500)
    assert loaded_snapshots[1].spot == pytest.approx(480)


def test_get_last_snapshot(tmp_path):
    """Vérifie que le dernier snapshot est bien renvoyé."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

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
        spot=470,
        implied_volatility=0.30,
        portfolio_value=850,
        delta=9.0,
        gamma=0.40,
        theta=-2.0,
        vega=18.0,
        rho=1.4
    )

    history.save_snapshot(first_snapshot)
    history.save_snapshot(second_snapshot)

    last_snapshot = history.get_last_snapshot()

    assert last_snapshot is not None
    assert last_snapshot.spot == pytest.approx(470)
    assert last_snapshot.implied_volatility == pytest.approx(0.30)


def test_get_last_snapshot_returns_none_when_empty(tmp_path):
    """Un historique vide ne doit pas renvoyer de snapshot."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    last_snapshot = history.get_last_snapshot()

    assert last_snapshot is None


def test_load_snapshots_returns_empty_list_when_file_does_not_exist(
    tmp_path
):
    """Un fichier inexistant correspond à un historique vide."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    snapshots = history.load_snapshots()

    assert snapshots == []


def test_clear_history_deletes_file(tmp_path, snapshot):
    """Vérifie que clear_history supprime bien le fichier CSV."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    history.save_snapshot(snapshot)

    assert file_path.exists()

    history.clear_history()

    assert not file_path.exists()


def test_clear_empty_history_does_not_raise_error(tmp_path):
    """Supprimer un historique inexistant ne doit pas provoquer d'erreur."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    history.clear_history()

    assert not file_path.exists()


def test_timestamp_is_preserved(tmp_path, snapshot):
    """Vérifie que la date est correctement sauvegardée puis relue."""

    file_path = tmp_path / "risk_history.csv"

    history = RiskHistory(
        file_path=str(file_path)
    )

    history.save_snapshot(snapshot)

    loaded_snapshot = history.load_snapshots()[0]

    assert loaded_snapshot.timestamp == snapshot.timestamp
