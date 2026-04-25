"""Tests for app.utils.rate_limit.

Covers:
  * parse_rate_limit — valid parsing and error handling.
  * ValkeyBucketStore / ValkeyFixedWindowBucket — allow/deny under fakeredis,
    header accuracy, EVALSHA script reuse.
  * Fail-open and fail-closed behaviour when the Valkey client raises.
  * rate_limit_headers — correctness across in-memory and Valkey buckets.
  * build_bucket_store — falls back to the in-memory limiter when the
    Valkey health-check ping fails.
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock

import fakeredis
import pytest

from app.utils import rate_limit as rate_limit_module
from app.utils.rate_limit import (
    BucketStore,
    TokenBucket,
    ValkeyBucketStore,
    ValkeyFixedWindowBucket,
    build_bucket_store,
    parse_rate_limit,
    rate_limit_headers,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patch_redis_with_fakeredis(monkeypatch: pytest.MonkeyPatch) -> fakeredis.FakeServer:
    """Redirect ``redis.from_url`` in the module to fakeredis-backed clients.

    Returns the shared fake server so tests can inspect stored keys if needed.
    All clients produced from the patched ``from_url`` share the same server,
    which mirrors how a real Valkey instance is shared across connections.
    """
    server = fakeredis.FakeServer()

    def _fake_from_url(url, **kwargs):  # noqa: ARG001 - url is unused on fake
        return fakeredis.FakeRedis(
            server=server,
            decode_responses=kwargs.get("decode_responses", True),
        )

    monkeypatch.setattr(rate_limit_module.redis, "from_url", _fake_from_url)
    return server


def _make_valkey_store(
    monkeypatch: pytest.MonkeyPatch,
    *,
    namespace: str = "test",
    capacity: int = 3,
    window_seconds: int = 60,
    fail_open: bool = True,
) -> ValkeyBucketStore:
    _patch_redis_with_fakeredis(monkeypatch)
    refill_rate = capacity / window_seconds
    return ValkeyBucketStore(
        namespace=namespace,
        capacity=capacity,
        refill_rate=refill_rate,
        url="redis://unused",
        fail_open=fail_open,
        window_seconds=window_seconds,
    )


# ---------------------------------------------------------------------------
# parse_rate_limit
# ---------------------------------------------------------------------------


class TestParseRateLimit:
    @pytest.mark.parametrize(
        "spec, expected",
        [
            ("10/minute", (10, 10 / 60, 60)),
            ("5/second", (5, 5.0, 1)),
            ("1/sec", (1, 1.0, 1)),
            ("100/hour", (100, 100 / 3600, 3600)),
            ("3/day", (3, 3 / 86400, 86400)),
            ("2/min", (2, 2 / 60, 60)),
            ("120/minute", (120, 2.0, 60)),
        ],
    )
    def test_valid_specs(self, spec, expected):
        capacity, refill_rate, window = parse_rate_limit(spec)
        assert capacity == expected[0]
        assert refill_rate == pytest.approx(expected[1])
        assert window == expected[2]

    def test_window_is_configured_value_not_derived(self):
        # Regression: window_seconds must come from the parsed window, not
        # from ``ceil(capacity / refill_rate)`` which is subject to float
        # rounding for non-power-of-two rates.
        _, _, window = parse_rate_limit("7/minute")
        assert window == 60

    @pytest.mark.parametrize(
        "bad",
        [
            "",
            "/minute",
            "10/",
            "abc/minute",
            "10/fortnight",
            "10/year",
            "10minute",
        ],
    )
    def test_invalid_formats_raise(self, bad):
        with pytest.raises(ValueError):
            parse_rate_limit(bad)

    @pytest.mark.parametrize("bad", ["0/minute", "-1/minute"])
    def test_non_positive_amount_raises(self, bad):
        with pytest.raises(ValueError):
            parse_rate_limit(bad)


# ---------------------------------------------------------------------------
# Valkey limiter — allow / deny
# ---------------------------------------------------------------------------


class TestValkeyLimiterAllowDeny:
    def test_allows_up_to_capacity_then_denies(self, monkeypatch):
        store = _make_valkey_store(monkeypatch, capacity=3, window_seconds=60)
        bucket = store["user-42"]

        assert bucket.allow() is True
        assert bucket.allow() is True
        assert bucket.allow() is True
        # The 4th call must be rejected because we are past capacity.
        denied = store["user-42"]
        assert denied.allow() is False

    def test_remaining_decreases_each_allow(self, monkeypatch):
        store = _make_valkey_store(monkeypatch, capacity=3, window_seconds=60)

        b1 = store["client"]
        b1.allow()
        assert b1.remaining() == 2

        b2 = store["client"]
        b2.allow()
        assert b2.remaining() == 1

        b3 = store["client"]
        b3.allow()
        assert b3.remaining() == 0

    def test_separate_keys_track_independent_counters(self, monkeypatch):
        store = _make_valkey_store(monkeypatch, capacity=2, window_seconds=60)

        a = store["alice"]
        assert a.allow() is True
        assert a.allow() is True
        # alice is at the limit
        assert store["alice"].allow() is False

        # bob is unaffected by alice's usage
        bob = store["bob"]
        assert bob.allow() is True
        assert bob.remaining() == 1

    def test_window_rollover_resets_counter(self, monkeypatch):
        store = _make_valkey_store(monkeypatch, capacity=2, window_seconds=60)

        # Freeze the clock used by the module to control window_id
        # computation. Using the attribute-path form keeps the patch scoped
        # to the rate_limit module's reference to ``time.time``.
        current = [1_700_000_000.0]
        monkeypatch.setattr(
            "app.utils.rate_limit.time.time", lambda: current[0]
        )

        b1 = store["user"]
        assert b1.allow() is True
        b2 = store["user"]
        assert b2.allow() is True
        # At capacity in the current window.
        assert store["user"].allow() is False

        # Jump forward past the window boundary — counter should reset.
        current[0] += 61
        assert store["user"].allow() is True


# ---------------------------------------------------------------------------
# Header accuracy
# ---------------------------------------------------------------------------


class TestRateLimitHeaders:
    def test_headers_after_allow(self, monkeypatch):
        store = _make_valkey_store(monkeypatch, capacity=5, window_seconds=60)
        bucket = store["k"]
        bucket.allow()

        headers = rate_limit_headers(bucket)
        assert headers["X-RateLimit-Limit"] == "5"
        assert headers["X-RateLimit-Remaining"] == "4"
        assert headers["Retry-After"] == "0"
        # Reset should reflect a TTL very close to the configured window
        # right after the INCR/EXPIRE that just ran.
        reset = int(headers["X-RateLimit-Reset"])
        assert 59 <= reset <= 60

    def test_headers_after_deny_show_zero_remaining_and_positive_retry(
        self, monkeypatch
    ):
        store = _make_valkey_store(monkeypatch, capacity=1, window_seconds=60)
        assert store["k"].allow() is True  # consume capacity

        denied_bucket = store["k"]
        assert denied_bucket.allow() is False

        headers = rate_limit_headers(denied_bucket)
        assert headers["X-RateLimit-Limit"] == "1"
        assert headers["X-RateLimit-Remaining"] == "0"
        assert int(headers["Retry-After"]) >= 1
        assert int(headers["X-RateLimit-Reset"]) >= 1

    def test_headers_for_in_memory_token_bucket(self):
        bucket = TokenBucket(capacity=3, refill_rate=1 / 20)
        assert bucket.allow() is True
        headers = rate_limit_headers(bucket)

        assert headers["X-RateLimit-Limit"] == "3"
        assert headers["X-RateLimit-Remaining"] == "2"
        assert headers["Retry-After"] == "0"


# ---------------------------------------------------------------------------
# Fail-open / fail-closed
# ---------------------------------------------------------------------------


def _raising_script(*args, **kwargs):  # noqa: ARG001
    raise ConnectionError("valkey is down")


class TestFailOpen:
    def test_allows_and_reports_full_capacity(self):
        bucket = ValkeyFixedWindowBucket(
            client=MagicMock(),
            namespace="ns",
            key="user",
            capacity=5,
            window_seconds=60,
            fail_open=True,
            limiter_script=_raising_script,
        )

        assert bucket.allow() is True
        headers = rate_limit_headers(bucket)
        assert headers["X-RateLimit-Limit"] == "5"
        assert headers["X-RateLimit-Remaining"] == "5"
        assert headers["Retry-After"] == "0"
        assert headers["X-RateLimit-Reset"] == "0"

    def test_header_lookup_after_allow_does_not_re_hit_dead_client(self):
        client = MagicMock()
        # If the cached state is used, no pipeline call should be issued.
        bucket = ValkeyFixedWindowBucket(
            client=client,
            namespace="ns",
            key="user",
            capacity=5,
            window_seconds=60,
            fail_open=True,
            limiter_script=_raising_script,
        )
        bucket.allow()
        _ = rate_limit_headers(bucket)
        client.pipeline.assert_not_called()


class TestFailClosed:
    def test_denies_and_reports_accurate_headers(self):
        bucket = ValkeyFixedWindowBucket(
            client=MagicMock(),
            namespace="ns",
            key="user",
            capacity=5,
            window_seconds=60,
            fail_open=False,
            limiter_script=_raising_script,
        )

        assert bucket.allow() is False
        headers = rate_limit_headers(bucket)

        # Regression: before the fix these headers showed full capacity and
        # Retry-After: 0 on a 429 response when Valkey was unreachable.
        assert headers["X-RateLimit-Limit"] == "5"
        assert headers["X-RateLimit-Remaining"] == "0"
        assert int(headers["Retry-After"]) == 60
        assert int(headers["X-RateLimit-Reset"]) == 60

    def test_header_lookup_does_not_re_hit_dead_client(self):
        client = MagicMock()
        bucket = ValkeyFixedWindowBucket(
            client=client,
            namespace="ns",
            key="user",
            capacity=5,
            window_seconds=60,
            fail_open=False,
            limiter_script=_raising_script,
        )
        bucket.allow()
        _ = rate_limit_headers(bucket)
        client.pipeline.assert_not_called()


# ---------------------------------------------------------------------------
# EVALSHA script reuse
# ---------------------------------------------------------------------------


class TestLuaScriptReuse:
    def test_script_registered_once_and_shared_across_buckets(self, monkeypatch):
        store = _make_valkey_store(monkeypatch, capacity=3, window_seconds=60)

        # Every bucket produced by the store must share the single registered
        # Script object — that is what allows redis-py to use EVALSHA instead
        # of shipping the script body on every request.
        b1 = store["alice"]
        b2 = store["bob"]
        assert b1._limiter_script is store._limiter_script
        assert b2._limiter_script is store._limiter_script
        assert b1._limiter_script is b2._limiter_script

    def test_register_script_called_exactly_once_per_store(self, monkeypatch):
        _patch_redis_with_fakeredis(monkeypatch)

        store = ValkeyBucketStore(
            namespace="test",
            capacity=3,
            refill_rate=0.05,
            url="redis://unused",
            window_seconds=60,
        )

        # Spy on register_script to make sure subsequent bucket accesses
        # don't trigger re-registration.
        register_spy = MagicMock(wraps=store.client.register_script)
        monkeypatch.setattr(store.client, "register_script", register_spy)

        for i in range(5):
            store[f"key-{i}"].allow()

        # register_script should not have been called again after __init__.
        register_spy.assert_not_called()


# ---------------------------------------------------------------------------
# build_bucket_store fallback
# ---------------------------------------------------------------------------


class TestBuildBucketStore:
    def test_returns_in_memory_when_valkey_url_is_unset(self, monkeypatch):
        monkeypatch.setattr(rate_limit_module.settings, "VALKEY_URL", None)
        store = build_bucket_store(
            "n", capacity=3, refill_rate=0.05, window_seconds=60
        )
        assert isinstance(store, BucketStore)

    def test_returns_valkey_when_url_set_and_reachable(self, monkeypatch):
        _patch_redis_with_fakeredis(monkeypatch)
        monkeypatch.setattr(
            rate_limit_module.settings, "VALKEY_URL", "redis://unused"
        )
        store = build_bucket_store(
            "n", capacity=3, refill_rate=0.05, window_seconds=60
        )
        assert isinstance(store, ValkeyBucketStore)

    def test_falls_back_when_ping_fails(self, monkeypatch):
        # Patch from_url to return a client whose ping raises — simulating
        # an unreachable Valkey instance at startup.
        class _BrokenClient:
            def ping(self):
                raise ConnectionError("unreachable")

            def register_script(self, script):  # pragma: no cover - never reached
                raise AssertionError("register_script must not run on a dead client")

        monkeypatch.setattr(
            rate_limit_module.redis,
            "from_url",
            lambda *a, **kw: _BrokenClient(),
        )
        monkeypatch.setattr(
            rate_limit_module.settings, "VALKEY_URL", "redis://unused"
        )

        store = build_bucket_store(
            "n", capacity=3, refill_rate=0.05, window_seconds=60
        )

        # The constructor should have raised inside build_bucket_store's
        # try/except, and build_bucket_store must return the in-memory store.
        assert isinstance(store, BucketStore)


# ---------------------------------------------------------------------------
# Sanity: window_seconds is honoured as-is, not recomputed from refill_rate
# ---------------------------------------------------------------------------


class TestWindowSecondsPlumbing:
    def test_explicit_window_seconds_is_preserved(self, monkeypatch):
        _patch_redis_with_fakeredis(monkeypatch)
        store = ValkeyBucketStore(
            namespace="n",
            capacity=10,
            # A deliberately "wrong" refill_rate that, if used to derive
            # the window, would yield a different value.
            refill_rate=0.01,
            url="redis://unused",
            window_seconds=42,
        )
        assert store.window_seconds == 42

    def test_defaults_to_ceil_when_window_seconds_missing(self, monkeypatch):
        _patch_redis_with_fakeredis(monkeypatch)
        store = ValkeyBucketStore(
            namespace="n",
            capacity=5,
            refill_rate=0.5,
            url="redis://unused",
        )
        assert store.window_seconds == max(1, math.ceil(5 / 0.5))
