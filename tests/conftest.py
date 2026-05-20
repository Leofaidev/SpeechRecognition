import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def english_10s_wav() -> Path:
    return FIXTURES_DIR / "english_10s.wav"


@pytest.fixture(scope="session")
def finnish_10s_wav() -> Path:
    return FIXTURES_DIR / "finnish_10s.wav"


@pytest.fixture(scope="session")
def two_speaker_30s_mp3() -> Path:
    return FIXTURES_DIR / "two_speaker_30s.mp3"


@pytest.fixture(scope="session")
def silent_wav() -> Path:
    return FIXTURES_DIR / "silent.wav"


@pytest.fixture(scope="session")
def noisy_wav() -> Path:
    return FIXTURES_DIR / "noisy.wav"


@pytest.fixture(scope="session")
def short_1s_wav() -> Path:
    return FIXTURES_DIR / "short_1s.wav"


# ---------------------------------------------------------------------------
# Custom CLI options — skip integration/performance tests unless opted in
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires real models downloaded locally)",
    )
    parser.addoption(
        "--performance",
        action="store_true",
        default=False,
        help="Run performance benchmarks (requires real models and real/synthetic audio)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    skip_it = pytest.mark.skip(reason="pass --integration to run integration tests")
    skip_pt = pytest.mark.skip(reason="pass --performance to run performance benchmarks")
    for item in items:
        if "integration" in item.keywords and not config.getoption("--integration"):
            item.add_marker(skip_it)
        if "performance" in item.keywords and not config.getoption("--performance"):
            item.add_marker(skip_pt)
