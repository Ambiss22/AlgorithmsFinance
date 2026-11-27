"""Proposed market-calibration interfaces; implementation is pending.

Inputs are already-validated consecutive hourly prices from prepare_data.py.
The caller must supply actual elapsed T in years; this price-only interface
cannot detect timestamp gaps and must not bridge them silently.
"""
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Calibration:
    """Outputs for direct use with the established scalar pricing interface."""
    N: int
    log_returns: tuple[float, ...]
    s: float
    u: float
    d: float
    R: float
    q: float


def log_returns(prices: Sequence[float]) -> tuple[float, ...]:
    """Return ln(P_i/P_(i-1)) in input order, for i=1,...,len(prices)-1.

    Require at least two positive finite prices; otherwise raise ValueError.
    Do not substitute arithmetic returns or returns relative to the first price.
    """
    raise NotImplementedError('Hourly logarithmic returns implementation is pending.')


def sample_hourly_volatility(returns: Sequence[float]) -> float:
    """Return the sample standard deviation of hourly LOG returns.

    For N returns, use sqrt(sum((r_i-mean(r))**2)/(N-1)). Require at least
    two finite returns; otherwise raise ValueError. Constant returns have s=0,
    even if their mean is nonzero. Do not annualize or rescale hourly s.
    """
    raise NotImplementedError('Sample hourly volatility implementation is pending.')


def calibrate_binomial(prices: Sequence[float], *, T: float, annual_rate: float = 0.04) -> Calibration:
    """Calibrate the lab tree and return immutable Calibration outputs.

    N=len(prices)-1, s=sample hourly log-return standard deviation,
    u=exp(s), d=1/u, R=exp(annual_rate*T/N), q=(R-d)/(u-d).
    T is actual elapsed years; annual_rate is continuously compounded.

    Require >=3 positive finite closes, finite T>0 and finite annual_rate.
    Raise ValueError for insufficient observations or invalid numeric inputs.
    Reject zero volatility with ValueError whose message mentions volatility:
    u=d=1 makes q undefined. Do not inject a volatility floor.
    Also reject nonfinite/degenerate factors and failures of 0<d<R<u (or
    0<q<1) with ValueError explaining no-arbitrage/probability. Never clip q.

    A nonzero constant log return still has zero volatility and is rejected.
    """
    raise NotImplementedError('Binomial market calibration implementation is pending.')