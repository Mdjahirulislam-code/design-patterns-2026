"""Strategy unit tests with plain contexts. No database, no HTTP."""

from uuid import uuid4

import pytest

from domain.automation.context import LocationAutomationContext
from domain.automation.errors import UnknownStrategyError
from domain.automation.strategy import (
    AggressiveMoistureStrategy,
    AutomationStrategy,
    ConservativeMoistureStrategy,
    available_strategies,
    get_strategy,
)


def context(moisture, low=0.25, high=0.45, has_sensor=True):
    return LocationAutomationContext(
        location_id=uuid4(),
        zone_id=uuid4(),
        zone_name="Zone 1",
        low=low,
        high=high,
        moisture=moisture,
        has_moisture_sensor=has_sensor,
    )


def test_conservative_waits_when_within_band():
    result = ConservativeMoistureStrategy().decide(context(0.35))

    assert result.action == "wait"
    assert result.reason == "Moisture 0.35 is within 0.25–0.45"


def test_aggressive_differs_on_same_context():
    same = context(0.35)

    conservative = get_strategy("conservative").decide(same)
    aggressive = get_strategy("aggressive").decide(same)

    assert conservative.action == "wait"
    assert aggressive.action == "irrigate"
    assert "0.35" in aggressive.reason
    assert aggressive.score > 0


def test_both_irrigate_below_the_low_threshold():
    dry = context(0.20)

    for key in ("conservative", "aggressive"):
        result = get_strategy(key).decide(dry)
        assert result.action == "irrigate"
        assert "below the low threshold 0.25" in result.reason


def test_aggressive_scores_higher_on_same_dry_context():
    dry = context(0.20)
    assert get_strategy("aggressive").decide(dry).score > get_strategy("conservative").decide(dry).score


@pytest.mark.parametrize("moisture", [0.45, 0.50])
def test_both_wait_at_or_above_the_high_threshold(moisture):
    for key in ("conservative", "aggressive"):
        assert get_strategy(key).decide(context(moisture)).action == "wait"


def test_thresholds_come_from_the_context_not_from_constants():
    # same moisture, different zone band -> different answer
    strategy = ConservativeMoistureStrategy()
    assert strategy.decide(context(0.30, low=0.25, high=0.45)).action == "wait"
    assert strategy.decide(context(0.30, low=0.35, high=0.60)).action == "irrigate"


def test_zone_without_moisture_sensor_waits():
    for key in ("conservative", "aggressive"):
        result = get_strategy(key).decide(context(None, has_sensor=False))
        assert result.action == "wait"
        assert result.reason == "No moisture sensor in this zone"


def test_zone_with_sensor_but_no_reading_waits():
    result = get_strategy("aggressive").decide(context(None, has_sensor=True))
    assert result.action == "wait"
    assert "No moisture reading" in result.reason


def test_unknown_strategy_key_is_rejected():
    with pytest.raises(UnknownStrategyError, match="Unknown strategy 'turbo'"):
        get_strategy("turbo")


def test_strategy_keys_are_normalized():
    assert isinstance(get_strategy(" Aggressive "), AggressiveMoistureStrategy)


def test_registry_lists_both_strategies_behind_one_interface():
    strategies = available_strategies()

    assert [s.key for s in strategies] == ["conservative", "aggressive"]
    assert all(isinstance(s, AutomationStrategy) for s in strategies)


def test_context_rejects_inverted_thresholds():
    with pytest.raises(ValueError):
        context(0.3, low=0.5, high=0.4)
