"""Shared pytest configuration.

`asyncio_mode = "auto"` is configured in `pyproject.toml` so that all
``async def test_*`` functions are picked up by ``pytest-asyncio`` without
needing per-test decorators.

The one shared fixture strips ambient proxy variables: ``Settings`` falls back
to the process-level ``HTTPS_PROXY`` for Discord traffic, so without this a
developer machine or CI runner that exports one would leak into every test
that builds a ``Settings``.
"""

from __future__ import annotations

import pytest

_AMBIENT_PROXY_VARS = (
    "DISCORD_PROXY",
    "HTTPS_PROXY",
    "https_proxy",
    "NO_PROXY",
    "no_proxy",
)


@pytest.fixture(autouse=True)
def _no_ambient_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove proxy variables inherited from the host for every test."""
    for name in _AMBIENT_PROXY_VARS:
        monkeypatch.delenv(name, raising=False)
