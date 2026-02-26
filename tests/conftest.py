import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests that require h5 data download",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: requires h5 data download (deselect with '-m \"not slow\"')")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="module")
def model_1d():
    """Load the 1D surrogate model (triggers h5 download)."""
    from BHPTNRSurrogate.surrogates import BHPTNRSur1dq1e4
    BHPTNRSur1dq1e4._ensure_loaded()
    return BHPTNRSur1dq1e4


@pytest.fixture(scope="module")
def model_2d():
    """Load the 2D surrogate model (triggers h5 download).

    Skips if the eval_pysur submodule (needed for GPR fits) is not available.
    """
    try:
        from BHPTNRSurrogate.surrogates.common_utils.eval_pysur import evaluate_fit  # noqa: F401
    except ImportError:
        pytest.skip(
            "eval_pysur submodule not available — run "
            "'git submodule init && git submodule update'"
        )
    from BHPTNRSurrogate.surrogates import BHPTNRSur2dq1e3
    BHPTNRSur2dq1e3._ensure_loaded()
    return BHPTNRSur2dq1e3
