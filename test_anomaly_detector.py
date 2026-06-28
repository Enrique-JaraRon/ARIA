from datetime import datetime

import pytest

from anomaly_detector import Alert, AnomalyDetector, RiskSnapshot


@pytest.fixture
def normal_snapshot():
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


@pytest.fixture
def stressed_snapshot():
    return RiskSnapshot(
        timestamp=datetime.now(),
        spot=460,
        implied_volatility=0.35,
        portfolio_value=800,
        delta=18.0,
        gamma=1.50,
        theta=-4.0,
        vega=30.0,
        rho=2.0
    )


@pytest.fixture
def detector():
    return AnomalyDetector(
        delta_limit=10.0,
        gamma_limit=1.0,
        vega_limit=20.0,
        daily_spot_move_limit=0.03,
        volatility_move_limit=0.05,
        z_score_limit=2.5
    )


def test_valid_snapshot_is_created(normal_snapshot):
    assert normal_snapshot.spot == 500
    assert normal_snapshot.implied_volatility == 0.20
    assert normal_snapshot.delta == 5.0


def test_invalid_spot_raises_error():
    with pytest.raises(ValueError):
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=0,
            implied_volatility=0.20,
            portfolio_value=1000,
            delta=5.0,
            gamma=0.20,
            theta=-1.0,
            vega=10.0,
            rho=1.0
        )


def test_invalid_volatility_raises_error():
    with pytest.raises(ValueError):
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=500,
            implied_volatility=0,
            portfolio_value=1000,
            delta=5.0,
            gamma=0.20,
            theta=-1.0,
            vega=10.0,
            rho=1.0
        )


def test_z_score_is_calculated_correctly(detector):
    history = [8.0, 9.0, 10.0, 11.0, 12.0]

    z_score = detector.calculate_z_score(
        current_value=15.0,
        historical_values=history
    )

    assert z_score is not None
    assert z_score > 1


def test_z_score_returns_none_with_insufficient_history(detector):
    z_score = detector.calculate_z_score(
        current_value=10.0,
        historical_values=[9.0]
    )

    assert z_score is None


def test_z_score_returns_none_when_variance_is_zero(detector):
    z_score = detector.calculate_z_score(
        current_value=10.0,
        historical_values=[5.0, 5.0, 5.0]
    )

    assert z_score is None


def test_normal_snapshot_does_not_trigger_exposure_alerts(
    detector,
    normal_snapshot
):
    alerts = detector.detect_exposure_limits(
        normal_snapshot
    )

    assert alerts == []


def test_high_delta_triggers_alert(
    detector,
    stressed_snapshot
):
    alerts = detector.detect_exposure_limits(
        stressed_snapshot
    )

    alert_names = [
        alert.name
        for alert in alerts
    ]

    assert "Exposition delta élevée" in alert_names


def test_high_gamma_triggers_alert(
    detector,
    stressed_snapshot
):
    alerts = detector.detect_exposure_limits(
        stressed_snapshot
    )

    alert_names = [
        alert.name
        for alert in alerts
    ]

    assert "Exposition gamma élevée" in alert_names


def test_high_vega_triggers_alert(
    detector,
    stressed_snapshot
):
    alerts = detector.detect_exposure_limits(
        stressed_snapshot
    )

    alert_names = [
        alert.name
        for alert in alerts
    ]

    assert "Exposition vega élevée" in alert_names


def test_large_spot_move_triggers_alert(detector):
    previous = RiskSnapshot(
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

    current = RiskSnapshot(
        timestamp=datetime.now(),
        spot=470,
        implied_volatility=0.20,
        portfolio_value=900,
        delta=6.0,
        gamma=0.25,
        theta=-1.2,
        vega=11.0,
        rho=1.1
    )

    alerts = detector.detect_market_moves(
        current=current,
        previous=previous
    )

    alert_names = [
        alert.name
        for alert in alerts
    ]

    assert "Mouvement important du sous-jacent" in alert_names


def test_large_volatility_move_triggers_alert(detector):
    previous = RiskSnapshot(
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

    current = RiskSnapshot(
        timestamp=datetime.now(),
        spot=500,
        implied_volatility=0.30,
        portfolio_value=1100,
        delta=5.5,
        gamma=0.22,
        theta=-1.1,
        vega=12.0,
        rho=1.1
    )

    alerts = detector.detect_market_moves(
        current=current,
        previous=previous
    )

    alert_names = [
        alert.name
        for alert in alerts
    ]

    assert "Variation importante de volatilité" in alert_names


def test_small_market_moves_do_not_trigger_alert(detector):
    previous = RiskSnapshot(
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

    current = RiskSnapshot(
        timestamp=datetime.now(),
        spot=505,
        implied_volatility=0.22,
        portfolio_value=1020,
        delta=5.2,
        gamma=0.21,
        theta=-1.1,
        vega=10.5,
        rho=1.1
    )

    alerts = detector.detect_market_moves(
        current=current,
        previous=previous
    )

    assert alerts == []


def test_historical_anomaly_is_detected(detector):
    history = [
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=500,
            implied_volatility=0.19,
            portfolio_value=1000,
            delta=5.0,
            gamma=0.20,
            theta=-1.0,
            vega=10.0,
            rho=1.0
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=502,
            implied_volatility=0.20,
            portfolio_value=1010,
            delta=5.2,
            gamma=0.21,
            theta=-1.1,
            vega=10.2,
            rho=1.1
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=498,
            implied_volatility=0.21,
            portfolio_value=990,
            delta=4.8,
            gamma=0.19,
            theta=-0.9,
            vega=9.8,
            rho=0.9
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=501,
            implied_volatility=0.20,
            portfolio_value=1005,
            delta=5.1,
            gamma=0.20,
            theta=-1.0,
            vega=10.1,
            rho=1.0
        )
    ]

    current = RiskSnapshot(
        timestamp=datetime.now(),
        spot=460,
        implied_volatility=0.35,
        portfolio_value=800,
        delta=18.0,
        gamma=1.50,
        theta=-4.0,
        vega=30.0,
        rho=2.0
    )

    alerts = detector.detect_historical_anomalies(
        current=current,
        history=history
    )

    assert len(alerts) > 0

    alert_names = [
        alert.name
        for alert in alerts
    ]

    assert "Delta inhabituel" in alert_names
    assert "Volatilité implicite inhabituelle" in alert_names


def test_detect_all_combines_all_alerts(
    detector,
    stressed_snapshot
):
    previous = RiskSnapshot(
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

    history = [
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=500,
            implied_volatility=0.19,
            portfolio_value=1000,
            delta=5.0,
            gamma=0.20,
            theta=-1.0,
            vega=10.0,
            rho=1.0
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=502,
            implied_volatility=0.20,
            portfolio_value=1010,
            delta=5.2,
            gamma=0.21,
            theta=-1.1,
            vega=10.2,
            rho=1.1
        ),
        RiskSnapshot(
            timestamp=datetime.now(),
            spot=498,
            implied_volatility=0.21,
            portfolio_value=990,
            delta=4.8,
            gamma=0.19,
            theta=-0.9,
            vega=9.8,
            rho=0.9
        )
    ]

    alerts = detector.detect_all(
        current=stressed_snapshot,
        history=history,
        previous=previous
    )

    assert len(alerts) >= 3


def test_alert_stores_information():
    alert = Alert(
        name="Test d'alerte",
        severity="ÉLEVÉE",
        message="Une valeur inhabituelle a été détectée.",
        current_value=15.0,
        reference_value=10.0,
        z_score=3.2
    )

    assert alert.name == "Test d'alerte"
    assert alert.severity == "ÉLEVÉE"
    assert alert.current_value == 15.0
    assert alert.reference_value == 10.0
    assert alert.z_score == 3.2


def test_severity_from_z_score(detector):
    assert detector.severity_from_z_score(2.6) == "MODÉRÉE"
    assert detector.severity_from_z_score(3.2) == "ÉLEVÉE"
    assert detector.severity_from_z_score(4.5) == "CRITIQUE"
