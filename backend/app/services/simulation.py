"""Offline characterization of the +/-1 adaptive ladder.

The production engine (:mod:`app.services.adaptive`) moves a learner's level up
by one on a correct answer and down by one on an incorrect one. This module
provides a **database-free** simulation that drives a synthetic learner of known
latent ability through that exact rule, so the ladder's behaviour can be
measured and reasoned about in tests and offline experiments.

The simple up/down rule is a classic *staircase* method: the presented
difficulty performs a bounded random walk that concentrates around the level at
which the learner is equally likely to be right or wrong. Under the logistic
response model used here, that 50%-correct level is exactly the learner's
ability, so the time-average of the presented levels estimates that ability
(with a small bias toward the interior near the level bounds). This is a
deliberately simple, transparent policy rather than a psychometric (IRT) model;
the harness exists to make its convergence explicit, not to claim more than the
rule delivers.

Run ``python -m app.services.simulation`` to print a convergence table.
"""

import math
import random
from dataclasses import dataclass


def probability_correct(ability: float, level: int, slope: float = 1.0) -> float:
    """Logistic probability that a learner answers a question correctly.

    ``ability`` and ``level`` share a single scale: the learner is a coin-flip
    when they are equal, more likely correct on easier (lower) levels and less
    likely correct on harder (higher) ones. ``slope`` controls how sharply that
    transition happens (larger = more deterministic).
    """
    return 1.0 / (1.0 + math.exp(-slope * (ability - level)))


def simulate_ladder(
    ability: float,
    *,
    min_level: int = 1,
    max_level: int = 5,
    start_level: int | None = None,
    steps: int = 400,
    slope: float = 1.0,
    seed: int = 0,
) -> list[int]:
    """Drive the +/-1 ladder against a synthetic learner and return level history.

    Element ``i`` of the result is the level of the question *presented* on step
    ``i``. The walk is clamped to ``[min_level, max_level]`` exactly as the live
    engine clamps it. The run is fully deterministic for a given ``seed``.
    """
    if max_level < min_level:
        raise ValueError("max_level must be >= min_level")
    if steps < 1:
        raise ValueError("steps must be >= 1")
    rng = random.Random(seed)
    level = min_level if start_level is None else start_level
    level = max(min_level, min(max_level, level))
    history: list[int] = []
    for _ in range(steps):
        history.append(level)
        if rng.random() < probability_correct(ability, level, slope):
            level = min(max_level, level + 1)
        else:
            level = max(min_level, level - 1)
    return history


def estimate_ability(history: list[int], burn_in: int = 0) -> float:
    """Estimate ability as the mean presented level after discarding ``burn_in``.

    The leading ``burn_in`` steps are dropped so the warm-up walk from the
    starting level does not bias the estimate.
    """
    tail = history[burn_in:]
    if not tail:
        raise ValueError("no steps remain after burn_in")
    return sum(tail) / len(tail)


@dataclass(frozen=True)
class ConvergenceResult:
    """Outcome of one simulated learner: where the ladder settled vs. the truth."""

    ability: float
    estimated_level: float
    absolute_error: float


def measure_convergence(
    ability: float,
    *,
    min_level: int = 1,
    max_level: int = 5,
    steps: int = 400,
    burn_in: int | None = None,
    slope: float = 1.0,
    seed: int = 0,
) -> ConvergenceResult:
    """Simulate one learner and report how close the ladder settles to ability.

    The error is measured against the ability *clamped to the level bounds*,
    since the ladder cannot represent an ability outside the range it offers.
    ``burn_in`` defaults to a quarter of ``steps``.
    """
    history = simulate_ladder(
        ability,
        min_level=min_level,
        max_level=max_level,
        steps=steps,
        slope=slope,
        seed=seed,
    )
    if burn_in is None:
        burn_in = steps // 4
    estimate = estimate_ability(history, burn_in)
    target = max(min_level, min(max_level, ability))
    return ConvergenceResult(
        ability=ability,
        estimated_level=estimate,
        absolute_error=abs(estimate - target),
    )


def main() -> int:
    """Print a convergence table for a spread of abilities on the 1-5 ladder."""
    print(f"{'ability':>8}  {'est. level':>10}  {'abs. error':>10}")
    for ability in (1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0):
        result = measure_convergence(ability, steps=2000, seed=7)
        print(
            f"{result.ability:>8.2f}  {result.estimated_level:>10.3f}  "
            f"{result.absolute_error:>10.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
