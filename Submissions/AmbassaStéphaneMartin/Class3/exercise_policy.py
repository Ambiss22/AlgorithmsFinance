"""Exercise-result and observed-decision contracts; production logic is pending.

The existing american_put.price_american_put scalar interface is unchanged.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class PutExerciseResult:
    price: float
    boundary: tuple[float | None, ...]


@dataclass(frozen=True)
class ObservedExercise:
    kind: Literal['early_exercise', 'maturity_settlement', 'never']
    index: int | None
    timestamp_utc: datetime | None
    payoff: float


def price_american_put_with_boundary(S0: float, K: float, u: float, d: float, R: float, N: int) -> PutExerciseResult:
    """Use the scalar pricer's six inputs and validation; additionally report boundary.

    boundary[t], t=0,...,N, is the highest stock among exercising nodes, or None
    if there is no exercising node. Length is N+1, including root and maturity.
    Before maturity exercise ONLY when intrinsic > continuation: exact ties,
    including 0 == 0, continue. At maturity positive-payoff nodes settle;
    zero-payoff nodes are not exercise nodes. Thus any numeric boundary is <K.
    For N=0, boundary[0] describes maturity, not an early-exercise opportunity.
    Return the same time-zero price as american_put.price_american_put.
    """
    raise NotImplementedError('Pricing with exercise boundary implementation is pending.')


def first_observed_exercise(prices: Sequence[float], boundary: Sequence[float | None], K: float,
                            *, timestamps_utc: Sequence[datetime]) -> ObservedExercise:
    """Map the indexed boundary onto an observed path with the same date axis.

    Scan t=0,...,N-1: the first non-None boundary with P_t<=boundary[t] and a
    positive payoff gives early_exercise. Boundary-price equality qualifies.
    Report its index, original UTC timestamp, and K-P_t.
    If no early exercise, a positive K-P_N gives maturity_settlement at N,
    regardless of whether the off-lattice observed price hits boundary[N].
    Otherwise return kind='never', index/timestamp=None, payoff=0.

    Exact NODE value ties continue; touching an already-classified exercise
    boundary qualifies. These are separate comparisons.
    Require nonempty equal-length prices/boundary/timestamps, positive finite
    prices, finite K>=0, UTC-aware strictly increasing dates, and boundaries
    that are None or finite positive values below K. Raise ValueError for
    invalid inputs. Missing exercise regions must use None, never zero or NaN.
    Timestamp gaps are handled by the calibration gate, not filled here.
    """
    raise NotImplementedError('Observed exercise decision implementation is pending.')