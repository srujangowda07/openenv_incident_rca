from __future__ import annotations
import enum


class CauseType(str, enum.Enum):
    # Core types (Legacy + New)
    CONNECTION_POOL_EXHAUSTED = "connection pool exhausted"
    MEMORY_LEAK_OOM = "memory leak OOMKilled"
    DISK_FULL = "disk full no log rotation"
    MISSING_INDEX = "missing index slow query"
    SPLIT_BRAIN = "cluster split-brain 2 nodes network partition"

    # New Task Types
    PERSISTENCE_CORRUPTION = "persistence file corruption"
    TEMP_FILE_OVERFLOW = "unbounded temporary files"
    PORT_CONFIG_MISMATCH = "port misconfiguration"
    CREDENTIALS_FAILURE = "database credentials failure"
    TLS_EXPIRY = "tls certificate expiry"
    DNS_CONFIG_ERROR = "dns misconfiguration"
    INDEX_CORRUPTION = "index corruption"
    CONFIG_DRIFT = "config drift"
    RATE_LIMITER_ERROR = "rate limiter failure"
    UNEXPECTED_FAILURE = "unexpected service failure"


CAUSE_MAPPINGS: dict[CauseType, list[str]] = {
    CauseType.CONNECTION_POOL_EXHAUSTED: [
        "pool exhausted",
        "max_connections",
        "hikari",
        "pgbouncer",
    ],
    CauseType.MEMORY_LEAK_OOM: [
        "oomkilled",
        "memory leak",
        "heap growth",
        "gc overhead",
    ],
    CauseType.DISK_FULL: [
        "disk full",
        "no space left",
        "disk usage 100",
        "log rotation",
    ],
    CauseType.MISSING_INDEX: [
        "missing index",
        "slow query",
        "full table scan",
        "dropped index",
    ],
    CauseType.SPLIT_BRAIN: [
        "split-brain",
        "split brain",
        "network partition",
        "no leader",
    ],
    CauseType.PERSISTENCE_CORRUPTION: [
        "persistence file corruption",
        "rdb file",
        "corrupt aof",
    ],
    CauseType.TEMP_FILE_OVERFLOW: [
        "temporary files",
        "temp cleanup",
        "disk full storage node",
    ],
    CauseType.PORT_CONFIG_MISMATCH: [
        "port misconfiguration",
        "targetport",
        "connection refused",
    ],
    CauseType.CREDENTIALS_FAILURE: [
        "credentials failure",
        "password authentication",
        "access denied",
    ],
    CauseType.TLS_EXPIRY: ["tls certificate expiry", "ssl handshake failed", "expired"],
    CauseType.DNS_CONFIG_ERROR: [
        "dns misconfiguration",
        "unknownhostexception",
        "coredns",
    ],
    CauseType.INDEX_CORRUPTION: [
        "index corruption",
        "corrupted page",
        "force_recovery",
    ],
    CauseType.CONFIG_DRIFT: ["config drift", "istio config", "proxy sync"],
    CauseType.RATE_LIMITER_ERROR: [
        "rate limiter failure",
        "429 rate",
        "token bucket overflow",
    ],
    CauseType.UNEXPECTED_FAILURE: [
        "unexpected service failure",
        "internal server error",
    ],
}

_PRIORITY_ORDER: list[CauseType] = list(CauseType)


def normalize_cause_type(raw_input: str) -> str:
    """
    Normalises an LLM-produced cause_type string into a canonical CauseType value.

    Matching strategy (in order):
      1. Direct exact match (case-insensitive, stripped).
      2. Multi-word phrase scoring   each phrase counts as +1.  A phrase only
         scores if it actually appears as a contiguous substring, preventing
         single common words from bleeding across unrelated categories.
      3. Ties are broken by _PRIORITY_ORDER (deterministic).
      4. If no phrase matches at all, the raw input is returned unchanged so
         the grader can surface a meaningful "unrecognised cause" message.
    """
    raw_lower = raw_input.lower().strip()

    for ct in CauseType:
        if ct.value == raw_lower:
            return ct.value
    scores: dict[CauseType, int] = {ct: 0 for ct in CauseType}
    for ct, phrases in CAUSE_MAPPINGS.items():
        scores[ct] = sum(1 for phrase in phrases if phrase in raw_lower)

    best_score = max(scores.values())
    if best_score == 0:
        return raw_input
    candidates = [ct for ct in _PRIORITY_ORDER if scores[ct] == best_score]
    return candidates[0].value


def normalize_service(raw_input: str) -> str:
    """Lower-case and strip whitespace for deterministic service name matching."""
    return raw_input.lower().strip()
