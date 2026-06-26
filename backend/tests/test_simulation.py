"""Tests for the offline convergence harness of the +/-1 adaptive ladder.

These exercise the pure simulation in :mod:`app.services.simulation`; no
database or web server is involved. All randomness is seeded, so the
assertions are deterministic.
"""

import math

import pytest

from app.services import simulation


def test_probability_is_a_coin_flip_when_ability_equals_level():
    assert simulation.probability_correct(3.0, 3) == pytest.approx(0.5)


def test_probability_decreases_with_harder_levels():
    p_easy = simulation.probability_correct(3.0, 1)
    p_mid = simulation.probability_correct(3.0, 3)
    p_hard = simulation.probability_correct(3.0, 5)
    assert p_easy > p_mid > p_hard
    assert 0.0 < p_hard and p_easy < 1.0


def test_slope_sharpens_the_response_curve():
    gentle = simulation.probability_correct(3.0, 1, slope=0.5)
    steep = simulation.probability_correct(3.0, 1, slope=3.0)
    assert steep > gentle  # a steeper slope is more confident on an easy item


def test_simulate_is_deterministic_for_a_seed():
    a = simulation.simulate_ladder(3.0, steps=200, seed=42)
    b = simulation.simulate_ladder(3.0, steps=200, seed=42)
    assert a == b


def test_simulate_respects_level_bounds():
    history = simulation.simulate_ladder(
        7.0, min_level=2, max_level=6, steps=500, seed=1
    )
    assert len(history) == 500
    assert all(2 <= level <= 6 for level in history)


def test_simulate_rejects_inverted_bounds():
    with pytest.raises(ValueError):
        simulation.simulate_ladder(3.0, min_level=5, max_level=1)


def test_simulate_rejects_nonpositive_steps():
    with pytest.raises(ValueError):
        simulation.simulate_ladder(3.0, steps=0)


def test_estimate_ability_drops_burn_in():
    assert simulation.estimate_ability([1, 1, 5, 5], burn_in=2) == pytest.approx(5.0)


def test_estimate_ability_rejects_empty_tail():
    with pytest.raises(ValueError):
        simulation.estimate_ability([1, 2, 3], burn_in=3)


def test_interior_ability_converges_on_the_one_to_five_ladder():
    # An ability squarely inside the range is recovered to well under half a level.
    result = simulation.measure_convergence(3.0, steps=2000, seed=7)
    assert result.absolute_error < 0.2


def test_interior_ability_converges_on_the_vocabulary_ladder():
    result = simulation.measure_convergence(
        6.0, min_level=1, max_level=10, steps=4000, seed=7
    )
    assert result.absolute_error < 0.2


def test_higher_ability_settles_at_a_higher_level():
    weak = simulation.measure_convergence(2.0, steps=2000, seed=7)
    strong = simulation.measure_convergence(4.0, steps=2000, seed=7)
    assert strong.estimated_level > weak.estimated_level


def test_ability_above_the_ceiling_pins_near_the_top():
    result = simulation.measure_convergence(
        10.0, min_level=1, max_level=5, steps=2000, seed=7
    )
    assert result.estimated_level > 4.5


def test_ability_below_the_floor_pins_near_the_bottom():
    result = simulation.measure_convergence(
        -5.0, min_level=1, max_level=5, steps=2000, seed=7
    )
    assert result.estimated_level < 1.5


def test_default_burn_in_is_a_quarter_of_steps():
    # With a flat history the estimate is trivially the level; this guards the
    # default burn_in wiring rather than the statistics.
    flat = simulation.simulate_ladder(100.0, min_level=4, max_level=4, steps=40, seed=0)
    assert flat == [4] * 40
    assert math.isclose(simulation.estimate_ability(flat, burn_in=10), 4.0)
