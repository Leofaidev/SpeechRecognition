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
