"""Regression test: BHPTNRSur1dq1e4 agreement between BHPTNRSurrogate and gwsurrogate.

Based on tutorials/testing_for_pr_no9.ipynb — both packages evaluate the same
underlying spline fits, so the waveforms should agree to machine precision.
"""

import warnings

import numpy as np
import pytest
from scipy.interpolate import interp1d


pytestmark = pytest.mark.gwsurrogate


gwsurrogate = pytest.importorskip("gwsurrogate")


MODES_TEST = [
    (2, 2), (2, 1), (3, 1), (3, 2), (3, 3),
    (4, 2), (4, 3), (4, 4), (5, 3), (5, 4), (5, 5),
]

ATOL_STRAIN = 1e-11
ATOL_PHASE = 1e-9


@pytest.fixture(scope="module")
def sur_bhpt():
    """Load BHPTNRSur1dq1e4 from the native package."""
    from BHPTNRSurrogate.surrogates import BHPTNRSur1dq1e4
    BHPTNRSur1dq1e4._ensure_loaded()
    return BHPTNRSur1dq1e4


@pytest.fixture(scope="module")
def sur_gw():
    """Load BHPTNRSur1dq1e4 via gwsurrogate."""
    import os
    gwsur_dir = os.path.join(os.path.dirname(gwsurrogate.__file__), "surrogate_downloads")
    gwsur_path = os.path.join(gwsur_dir, "BHPTNRSur1dq1e4.h5")
    if not os.path.exists(gwsur_path):
        gwsur_path = gwsurrogate.catalog.pull("BHPTNRSur1dq1e4")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sur = gwsurrogate.EvaluateSurrogate(gwsur_path)
    return sur


def _gwsur_to_dict(modes_gw, hp_gw, hc_gw):
    """Convert gwsurrogate output arrays to a mode dict using hp - 1j*hc convention."""
    h = {}
    for i, mode in enumerate(modes_gw):
        hp_m = hp_gw[:, i] if hp_gw.ndim > 1 else hp_gw
        hc_m = hc_gw[:, i] if hc_gw.ndim > 1 else hc_gw
        h[tuple(mode)] = hp_m - 1j * hc_m
    return h


def _compare_on_common_grid(t_bhpt, h_bhpt, t_gw, h_gw, modes):
    """Interpolate onto a common time grid and return max differences per mode."""
    t_lo = max(t_bhpt[0], t_gw[0])
    t_hi = min(t_bhpt[-1], t_gw[-1])

    if len(t_bhpt) == len(t_gw) and np.allclose(t_bhpt, t_gw, atol=1e-10):
        tc = t_bhpt
        h1 = h_bhpt
        h2 = h_gw
    else:
        mask = (t_bhpt >= t_lo) & (t_bhpt <= t_hi)
        tc = t_bhpt[mask]
        h1 = {m: h_bhpt[m][mask] for m in modes}
        h2 = {}
        for m in modes:
            h2[m] = (
                interp1d(t_gw, h_gw[m].real, "cubic")(tc)
                + 1j * interp1d(t_gw, h_gw[m].imag, "cubic")(tc)
            )

    results = {}
    for mode in modes:
        h1m, h2m = h1[mode], h2[mode]
        max_dh = np.max(np.abs(h1m - h2m))
        a1, a2 = np.abs(h1m), np.abs(h2m)
        thr = 1e-8 * max(np.max(a1), np.max(a2))
        valid = (a1 > thr) & (a2 > thr)
        if np.any(valid):
            max_dphi = np.max(np.abs(
                np.unwrap(np.angle(h1m[valid])) - np.unwrap(np.angle(h2m[valid]))
            ))
        else:
            max_dphi = 0.0
        results[mode] = {"max_dh": max_dh, "max_dphi": max_dphi}
    return results


@pytest.mark.parametrize("q", [3, 10, 100])
def test_bhpt_vs_gwsurrogate(sur_bhpt, sur_gw, q):
    """Waveforms from BHPTNRSurrogate and gwsurrogate should agree to machine precision."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        t_bhpt, h_bhpt = sur_bhpt.generate_surrogate(
            q=q, modes=MODES_TEST, neg_modes=False,
        )
        modes_gw, t_gw, hp_gw, hc_gw = sur_gw(
            q, mode_sum=False, fake_neg_modes=False,
        )

    h_gw = _gwsur_to_dict(modes_gw, hp_gw, hc_gw)
    common = sorted(set(h_bhpt.keys()) & set(h_gw.keys()))
    assert len(common) > 0, "No common modes between the two packages"

    diffs = _compare_on_common_grid(t_bhpt, h_bhpt, t_gw, h_gw, common)

    for mode, d in diffs.items():
        assert d["max_dh"] < ATOL_STRAIN, (
            f"q={q} mode={mode}: max|dh| = {d['max_dh']:.4e} exceeds {ATOL_STRAIN}"
        )
        assert d["max_dphi"] < ATOL_PHASE, (
            f"q={q} mode={mode}: max|dphi| = {d['max_dphi']:.4e} exceeds {ATOL_PHASE}"
        )
