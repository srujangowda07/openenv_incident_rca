from __future__ import annotations
import random
from datetime import datetime, timedelta


class ScenarioGenerator:
    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def generate(self, task_id: str) -> dict:
        try:
            difficulty, idx_str = task_id.split("_")
            idx = int(idx_str) - 1
            if difficulty == "easy":
                return self._generate_easy(idx)
            elif difficulty == "medium":
                return self._generate_medium(idx)
            elif difficulty == "hard":
                return self._generate_hard(idx)
            else:
                return self._fallback_easy()
        except Exception:
            return self._fallback_easy()

    def _generate_easy(self, idx: int) -> dict:
        scenarios = [
            self._easy_db_pool,
            self._easy_oom,
            self._easy_disk,
            self._easy_redis_crash,
            self._easy_disk_full_v2,
            self._easy_port_config,
            self._easy_credentials,
        ]
        return scenarios[idx % len(scenarios)]()

    def _generate_medium(self, idx: int) -> dict:
        scenarios = [
            self._medium_slow_query,
            self._medium_pool_exhaustion,
            self._medium_memory_leak,
            self._medium_tls_expiry,
            self._medium_dns_config,
        ]
        return scenarios[idx % len(scenarios)]()

    def _generate_hard(self, idx: int) -> dict:
        scenarios = [
            self._hard_redis_split_brain,
            self._hard_index_corruption,
            self._hard_distributed_split_brain,
            self._hard_config_drift,
            self._hard_rate_limiter,
        ]
        return scenarios[idx % len(scenarios)]()

    def _fallback_easy(self) -> dict:
        return {
            "description": "Critical system degradation: api-server unresponsive. Standard diagnostic required.",
            "alerts": [
                {
                    "id": "ALT-999",
                    "service": "api-server",
                    "severity": "critical",
                    "message": "Health check failed",
                }
            ],
            "services": [{"name": "api-server", "status": "unhealthy", "calls": []}],
            "dependency_graph": {"api-server": []},
            "logs": [
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "service": "api-server",
                    "level": "ERROR",
                    "message": "Internal Server Error",
                }
            ],
            "metrics": [
                {
                    "service": "api-server",
                    "metric": "error_rate",
                    "values": [1.0],
                    "unit": "ratio",
                    "timestamps": ["00:00"],
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "api-server",
                "cause_type": "unexpected service failure",
                "trigger": "unknown environmental change",
                "valid_fixes": ["restart service", "check logs"],
                "cascade": ["api-server"],
            },
        }

    # --- EASY TEMPLATES ---

    def _easy_db_pool(self) -> dict:
        base = datetime(2026, 3, 15, 14, 30, 0)
        return {
            "description": "INCIDENT ALERT: api-gateway returning 502. user-service latency high.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "api-gateway",
                    "severity": "critical",
                    "message": "502 error rate > 35%",
                    "time": "14:32:05",
                },
                {
                    "id": "ALT-002",
                    "service": "user-service",
                    "severity": "warning",
                    "message": "latency p99 > 5s",
                    "time": "14:32:10",
                },
            ],
            "services": [
                {
                    "name": "api-gateway",
                    "status": "degraded",
                    "calls": ["user-service"],
                },
                {
                    "name": "user-service",
                    "status": "degraded",
                    "calls": ["postgres-primary"],
                },
                {"name": "postgres-primary", "status": "unhealthy", "calls": []},
            ],
            "dependency_graph": {
                "api-gateway": ["user-service"],
                "user-service": ["postgres-primary"],
                "postgres-primary": [],
            },
            "logs": [
                self._log(
                    base,
                    -3,
                    "postgres-primary",
                    "ERROR",
                    "Connection pool exhausted: max_connections=100 reached",
                ),
                self._log(
                    base, -2, "user-service", "ERROR", "Failed to acquire DB connection"
                ),
            ],
            "metrics": [
                {
                    "service": "postgres-primary",
                    "metric": "active_connections",
                    "values": [90, 95, 100],
                    "unit": "count",
                    "timestamps": self._ts(base, 3),
                }
            ],
            "traces": {
                "req-1": [
                    {"service": "user-service", "duration_ms": 5000, "status": "error"}
                ]
            },
            "root_cause": {
                "service": "postgres-primary",
                "cause_type": "connection pool exhausted",
                "trigger": "unoptimized query leak",
                "valid_fixes": ["increase max_connections", "restart pgbouncer"],
                "cascade": ["postgres-primary", "user-service"],
            },
        }

    def _easy_oom(self) -> dict:
        base = datetime(2026, 3, 16, 9, 15, 0)
        return {
            "description": "INCIDENT ALERT: payment-service pods OOMKilled.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "payment-service",
                    "severity": "critical",
                    "message": "OOMKilled",
                    "time": "09:16:00",
                }
            ],
            "services": [
                {
                    "name": "checkout-api",
                    "status": "degraded",
                    "calls": ["payment-service"],
                },
                {"name": "payment-service", "status": "crashing", "calls": []},
            ],
            "dependency_graph": {
                "checkout-api": ["payment-service"],
                "payment-service": [],
            },
            "logs": [
                self._log(
                    base,
                    -1,
                    "payment-service",
                    "CRITICAL",
                    "OOMKilled: memory limit 1024Mi exceeded",
                )
            ],
            "metrics": [
                {
                    "service": "payment-service",
                    "metric": "memory_usage",
                    "values": [800, 950, 1024, 0],
                    "unit": "MB",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "payment-service",
                "cause_type": "memory leak OOMKilled",
                "trigger": "unbounded cache growth",
                "valid_fixes": ["increase memory limits", "rollback deploy"],
                "cascade": ["payment-service"],
            },
        }

    def _easy_disk(self) -> dict:
        base = datetime(2026, 3, 17, 22, 0, 0)
        return {
            "description": "INCIDENT ALERT: logging-service disk full.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "logging-service",
                    "severity": "critical",
                    "message": "Disk 100% full",
                    "time": "22:00:10",
                }
            ],
            "services": [
                {"name": "logging-service", "status": "degraded", "calls": []}
            ],
            "dependency_graph": {"logging-service": []},
            "logs": [
                self._log(
                    base, 0, "logging-service", "CRITICAL", "No space left on device"
                )
            ],
            "metrics": [
                {
                    "service": "logging-service",
                    "metric": "disk_usage",
                    "values": [95, 99, 100],
                    "unit": "percent",
                    "timestamps": self._ts(base, 3),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "logging-service",
                "cause_type": "disk full no log rotation",
                "trigger": "logrotate failure",
                "valid_fixes": ["clear /var/log", "add log rotation"],
                "cascade": ["logging-service"],
            },
        }

    def _easy_redis_crash(self) -> dict:
        base = datetime(2026, 3, 20, 10, 0, 0)
        return {
            "description": "INCIDENT ALERT: Redis-cache crash loop. session-service degraded.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "redis-cache",
                    "severity": "critical",
                    "message": "CrashLoopBackOff",
                    "time": "10:02:00",
                }
            ],
            "services": [
                {
                    "name": "session-service",
                    "status": "degraded",
                    "calls": ["redis-cache"],
                },
                {"name": "redis-cache", "status": "unhealthy", "calls": []},
            ],
            "dependency_graph": {"session-service": ["redis-cache"], "redis-cache": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "redis-cache",
                    "ERROR",
                    "Failed to load RDB file: unexpected end of file",
                )
            ],
            "metrics": [
                {
                    "service": "redis-cache",
                    "metric": "up",
                    "values": [1, 1, 0, 0, 1, 0],
                    "unit": "bool",
                    "timestamps": self._ts(base, 6),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "redis-cache",
                "cause_type": "persistence file corruption",
                "trigger": "improper shutdown",
                "valid_fixes": ["clear redis storage", "restart with empty db"],
                "cascade": ["redis-cache", "session-service"],
            },
        }

    def _easy_disk_full_v2(self) -> dict:
        # Same logic as disk but different service
        base = datetime(2026, 3, 21, 15, 0, 0)
        return {
            "description": "INCIDENT ALERT: storage-node-3 disk capacity 100%.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "storage-node-3",
                    "severity": "critical",
                    "message": "Disk usage critical",
                    "time": "15:05:00",
                }
            ],
            "services": [
                {"name": "storage-node-3", "status": "unhealthy", "calls": []}
            ],
            "dependency_graph": {"storage-node-3": []},
            "logs": [
                self._log(base, 0, "storage-node-3", "ERROR", "IOException: Disk full")
            ],
            "metrics": [
                {
                    "service": "storage-node-3",
                    "metric": "disk_free",
                    "values": [100, 50, 10, 0],
                    "unit": "MB",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "storage-node-3",
                "cause_type": "unbounded temporary files",
                "trigger": "temp cleanup job failed",
                "valid_fixes": ["clean /tmp", "increase disk size"],
                "cascade": ["storage-node-3"],
            },
        }

    def _easy_port_config(self) -> dict:
        base = datetime(2026, 3, 22, 12, 0, 0)
        return {
            "description": "INCIDENT ALERT: auth-service unreachable on port 8080.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "auth-service",
                    "severity": "critical",
                    "message": "TargetPort mismatch",
                    "time": "12:01:00",
                }
            ],
            "services": [
                {"name": "api-server", "status": "degraded", "calls": ["auth-service"]},
                {"name": "auth-service", "status": "healthy", "calls": []},
            ],
            "dependency_graph": {"api-server": ["auth-service"], "auth-service": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "api-server",
                    "ERROR",
                    "Connection refused on auth-service:8080",
                )
            ],
            "metrics": [
                {
                    "service": "auth-service",
                    "metric": "network_errors",
                    "values": [0, 0, 100, 100],
                    "unit": "count",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "auth-service",
                "cause_type": "port misconfiguration",
                "trigger": "config update changed container port to 8081",
                "valid_fixes": ["update service selector port", "revert port change"],
                "cascade": ["auth-service", "api-server"],
            },
        }

    def _easy_credentials(self) -> dict:
        base = datetime(2026, 3, 23, 8, 0, 0)
        return {
            "description": "INCIDENT ALERT: billing-service DB authentication failure.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "billing-service",
                    "severity": "critical",
                    "message": "DB Access Denied",
                    "time": "08:05:00",
                }
            ],
            "services": [
                {
                    "name": "billing-service",
                    "status": "unhealthy",
                    "calls": ["billing-db"],
                },
                {"name": "billing-db", "status": "healthy", "calls": []},
            ],
            "dependency_graph": {"billing-service": ["billing-db"], "billing-db": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "billing-service",
                    "ERROR",
                    "FATAL: password authentication failed for user 'billing_app'",
                )
            ],
            "metrics": [
                {
                    "service": "billing-service",
                    "metric": "db_conn_errors",
                    "values": [0, 1, 5, 20],
                    "unit": "count",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "billing-service",
                "cause_type": "database credentials failure",
                "trigger": "password rotation without updating secret",
                "valid_fixes": ["update kubernetes secret", "rollback password change"],
                "cascade": ["billing-service"],
            },
        }

    # --- MEDIUM TEMPLATES ---

    def _medium_slow_query(self) -> dict:
        base = datetime(2026, 3, 18, 11, 0, 0)
        return {
            "description": "INCIDENT ALERT: search-api p99 high. mysql load high.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "search-api",
                    "severity": "warning",
                    "message": "p99 > 8s",
                    "time": "11:03:00",
                }
            ],
            "services": [
                {"name": "search-api", "status": "degraded", "calls": ["mysql-repl"]},
                {"name": "mysql-repl", "status": "degraded", "calls": []},
            ],
            "dependency_graph": {"search-api": ["mysql-repl"], "mysql-repl": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "mysql-repl",
                    "WARN",
                    "Slow query: 12000ms SELECT * FROM items WHERE tags LIKE '%X%'",
                )
            ],
            "metrics": [
                {
                    "service": "mysql-repl",
                    "metric": "cpu_util",
                    "values": [20, 80, 95],
                    "unit": "percent",
                    "timestamps": self._ts(base, 3),
                }
            ],
            "traces": {
                "t-1": [{"service": "mysql-repl", "duration_ms": 12000, "status": "slow"}]
            },
            "root_cause": {
                "service": "mysql-repl",
                "cause_type": "missing index slow query",
                "trigger": "new feature filtering on non-indexed tags",
                "valid_fixes": ["add index", "rewrite query"],
                "cascade": ["mysql-repl", "search-api"],
            },
        }

    def _medium_pool_exhaustion(self) -> dict:
        base = datetime(2026, 3, 24, 14, 0, 0)
        return {
            "description": "INCIDENT ALERT: order-service connection pool saturation.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "order-service",
                    "severity": "critical",
                    "message": "Connection Pool Exhausted",
                    "time": "14:05:00",
                }
            ],
            "services": [
                {"name": "order-service", "status": "degraded", "calls": ["order-db"]},
                {"name": "order-db", "status": "healthy", "calls": []},
            ],
            "dependency_graph": {"order-service": ["order-db"], "order-db": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "order-service",
                    "ERROR",
                    "HikariPool-1 - Connection is not available, request timed out",
                )
            ],
            "metrics": [
                {
                    "service": "order-service",
                    "metric": "pool_active",
                    "values": [5, 15, 20, 20],
                    "unit": "count",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "order-service",
                "cause_type": "connection pool exhaustion",
                "trigger": "peak traffic exceeded default pool size of 20",
                "valid_fixes": ["increase pool size", "optimize query latency"],
                "cascade": ["order-service"],
            },
        }

    def _medium_memory_leak(self) -> dict:
        base = datetime(2026, 3, 25, 9, 0, 0)
        return {
            "description": "INCIDENT ALERT: recommendation-engine steady heap growth.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "recommendation-engine",
                    "severity": "warning",
                    "message": "Heap usage > 90%",
                    "time": "09:30:00",
                }
            ],
            "services": [
                {"name": "recommendation-engine", "status": "degraded", "calls": []}
            ],
            "dependency_graph": {"recommendation-engine": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "recommendation-engine",
                    "WARN",
                    "Java heap space low, GC overhead limit exceeded",
                )
            ],
            "metrics": [
                {
                    "service": "recommendation-engine",
                    "metric": "heap_usage",
                    "values": [200, 400, 600, 800, 950],
                    "unit": "MB",
                    "timestamps": self._ts(base, 5),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "recommendation-engine",
                "cause_type": "memory leak OOMKilled",
                "trigger": "static object map holding references indefinitely",
                "valid_fixes": ["restart pods", "fix code leak"],
                "cascade": ["recommendation-engine"],
            },
        }

    def _medium_tls_expiry(self) -> dict:
        base = datetime(2026, 3, 26, 0, 0, 0)
        return {
            "description": "INCIDENT ALERT: api-gateway TLS certificate expired.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "api-gateway",
                    "severity": "critical",
                    "message": "SSL Handshake Failed",
                    "time": "00:01:00",
                }
            ],
            "services": [{"name": "api-gateway", "status": "unhealthy", "calls": []}],
            "dependency_graph": {"api-gateway": []},
            "logs": [
                self._log(
                    base, 0, "api-gateway", "ERROR", "SSL error: certificate_expired"
                )
            ],
            "metrics": [
                {
                    "service": "api-gateway",
                    "metric": "cert_days_left",
                    "values": [2, 1, 0, 0],
                    "unit": "days",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "api-gateway",
                "cause_type": "tls certificate expiry",
                "trigger": "cert-manager challenge failed for renewal",
                "valid_fixes": ["manually update secret", "fix dns challenge"],
                "cascade": ["api-gateway"],
            },
        }

    def _medium_dns_config(self) -> dict:
        base = datetime(2026, 3, 27, 16, 0, 0)
        return {
            "description": "INCIDENT ALERT: internal-proxy DNS resolution failure.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "internal-proxy",
                    "severity": "critical",
                    "message": "UnknownHostException",
                    "time": "16:05:00",
                }
            ],
            "services": [
                {
                    "name": "internal-proxy",
                    "status": "unhealthy",
                    "calls": ["backend-svc"],
                },
                {"name": "backend-svc", "status": "healthy", "calls": []},
            ],
            "dependency_graph": {"internal-proxy": ["backend-svc"], "backend-svc": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "internal-proxy",
                    "ERROR",
                    "lookup backend-svc.cluster.local on 10.96.0.10:53: no such host",
                )
            ],
            "metrics": [
                {
                    "service": "internal-proxy",
                    "metric": "dns_errors",
                    "values": [0, 0, 50, 100],
                    "unit": "count",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "internal-proxy",
                "cause_type": "dns misconfiguration",
                "trigger": "CoreDNS configmap corrupted during update",
                "valid_fixes": ["fix coredns config", "restart coredns"],
                "cascade": ["internal-proxy"],
            },
        }

    # --- HARD TEMPLATES ---

    def _hard_redis_split_brain(self) -> dict:
        base = datetime(2026, 3, 19, 3, 0, 0)
        return {
            "description": "CRITICAL P0: Redis cluster split-brain. Multiple services affected.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "redis-cluster",
                    "severity": "critical",
                    "message": "split-brain detected",
                    "time": "03:01:45",
                },
                {
                    "id": "ALT-002",
                    "service": "auth-svc",
                    "severity": "critical",
                    "message": "redis unreachable",
                    "time": "03:02:00",
                },
            ],
            "services": [
                {
                    "name": "api",
                    "status": "degraded",
                    "calls": ["auth-svc", "session-svc"],
                },
                {"name": "auth-svc", "status": "unhealthy", "calls": ["redis-cluster"]},
                {
                    "name": "session-svc",
                    "status": "unhealthy",
                    "calls": ["redis-cluster"],
                },
                {"name": "redis-cluster", "status": "split-brain", "calls": []},
            ],
            "dependency_graph": {
                "api": ["auth-svc", "session-svc"],
                "auth-svc": ["redis-cluster"],
                "session-svc": ["redis-cluster"],
                "redis-cluster": [],
            },
            "logs": [
                self._log(
                    base,
                    0,
                    "redis-cluster",
                    "CRITICAL",
                    "CLUSTER INFO: cluster_state=fail — split-brain",
                )
            ],
            "metrics": [
                {
                    "service": "redis-cluster",
                    "metric": "nodes_healthy",
                    "values": [6, 6, 3],
                    "unit": "count",
                    "timestamps": self._ts(base, 3),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "redis-cluster",
                "cause_type": "cluster split-brain 2 nodes network partition",
                "trigger": "network switch failure isolated rack-A",
                "valid_fixes": ["recover switch", "force cluster reset"],
                "cascade": ["redis-cluster", "auth-svc", "session-svc", "api"],
            },
        }

    def _hard_index_corruption(self) -> dict:
        base = datetime(2026, 3, 28, 4, 0, 0)
        return {
            "description": "INCIDENT ALERT: data-inconsistency in user-reporting. MySQL index corruption.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "report-svc",
                    "severity": "critical",
                    "message": "Data parity check failed",
                    "time": "04:10:00",
                }
            ],
            "services": [
                {"name": "report-svc", "status": "degraded", "calls": ["mysql-repl"]},
                {"name": "mysql-repl", "status": "healthy", "calls": []},
            ],
            "dependency_graph": {"report-svc": ["mysql-repl"], "mysql-repl": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "mysql-repl",
                    "ERROR",
                    "Innodb: Found corrupted page [page id: space=123, page number=456]",
                )
            ],
            "metrics": [
                {
                    "service": "mysql-repl",
                    "metric": "corrupted_pages",
                    "values": [0, 0, 1, 5],
                    "unit": "count",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "mysql-repl",
                "cause_type": "index corruption",
                "trigger": "underlying storage hardware block failure",
                "valid_fixes": ["rebuild index", "run innodb_force_recovery"],
                "cascade": ["mysql-repl", "report-svc"],
            },
        }

    def _hard_distributed_split_brain(self) -> dict:
        base = datetime(2026, 3, 29, 2, 0, 0)
        return {
            "description": "CRITICAL P0: Etcd cluster split-brain. Control plane partitioned.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "etcd",
                    "severity": "critical",
                    "message": "no leader detected",
                    "time": "02:05:00",
                }
            ],
            "services": [
                {"name": "kube-apiserver", "status": "unhealthy", "calls": ["etcd"]},
                {"name": "etcd", "status": "split-brain", "calls": []},
            ],
            "dependency_graph": {"kube-apiserver": ["etcd"], "etcd": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "etcd",
                    "ERROR",
                    "raft.node: 1 [term: 10] ignored a MsgVote from 2 [term: 10] because it already has a leader",
                )
            ],
            "metrics": [
                {
                    "service": "etcd",
                    "metric": "has_leader",
                    "values": [1, 1, 0, 0],
                    "unit": "bool",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "etcd",
                "cause_type": "cluster split-brain 2 nodes network partition",
                "trigger": "multi-AZ link failure",
                "valid_fixes": ["restore az link", "re-bootstrap etcd"],
                "cascade": ["etcd", "kube-apiserver"],
            },
        }

    def _hard_config_drift(self) -> dict:
        base = datetime(2026, 3, 30, 20, 0, 0)
        return {
            "description": "INCIDENT ALERT: inconsistent routing in k8s-mesh. Istio config drift.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "istio-pilot",
                    "severity": "warning",
                    "message": "Push failures low but persistent",
                    "time": "20:15:00",
                }
            ],
            "services": [
                {
                    "name": "gateway",
                    "status": "degraded",
                    "calls": ["service-a", "service-b", "istio-pilot"],
                },
                {"name": "istio-pilot", "status": "unhealthy", "calls": []},
                {"name": "service-a", "status": "healthy", "calls": []},
                {"name": "service-b", "status": "healthy", "calls": []},
            ],
            "dependency_graph": {
                "gateway": ["service-a", "service-b", "istio-pilot"],
                "istio-pilot": [],
                "service-a": [],
                "service-b": [],
            },
            "logs": [
                self._log(
                    base,
                    0,
                    "istio-pilot",
                    "WARN",
                    "Config drift detected on proxy node-42: ADS push timeout",
                )
            ],
            "metrics": [
                {
                    "service": "istio-pilot",
                    "metric": "proxy_sync_errors",
                    "values": [0, 5, 12, 12],
                    "unit": "count",
                    "timestamps": self._ts(base, 4),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "istio-pilot",
                "cause_type": "config drift",
                "trigger": "partial deployment failure left some proxies on v1.2 and others on v1.3",
                "valid_fixes": ["restart envoys", "resync mesh config"],
                "cascade": ["istio-pilot", "gateway"],
            },
        }

    def _hard_rate_limiter(self) -> dict:
        base = datetime(2026, 3, 31, 11, 0, 0)
        return {
            "description": "INCIDENT ALERT: global-throttle-service dropping valid traffic. Rate limiter failure.",
            "alerts": [
                {
                    "id": "ALT-001",
                    "service": "global-throttle-service",
                    "severity": "critical",
                    "message": "429 rate > 50%",
                    "time": "11:05:00",
                }
            ],
            "services": [
                {"name": "ingress", "status": "degraded", "calls": ["global-throttle-service"]},
                {"name": "global-throttle-service", "status": "unhealthy", "calls": []},
            ],
            "dependency_graph": {"ingress": ["global-throttle-service"], "global-throttle-service": []},
            "logs": [
                self._log(
                    base,
                    0,
                    "global-throttle-service",
                    "ERROR",
                    "Rate-limiting logic error: bucket negative overflow",
                )
            ],
            "metrics": [
                {
                    "service": "global-throttle-service",
                    "metric": "throttle_rate",
                    "values": [0, 50, 95],
                    "unit": "percent",
                    "timestamps": self._ts(base, 3),
                }
            ],
            "traces": {},
            "root_cause": {
                "service": "global-throttle-service",
                "cause_type": "rate limiter failure",
                "trigger": "integer overflow in token bucket math",
                "valid_fixes": ["hotfix overflow logic", "bypass throttle-svc"],
                "cascade": ["global-throttle-service", "ingress"],
            },
        }

    @staticmethod
    def _log(
        base: datetime, offset_min: int, service: str, level: str, message: str
    ) -> dict:
        t = base + timedelta(minutes=offset_min)
        return {
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "service": service,
            "level": level,
            "message": message,
        }

    @staticmethod
    def _ts(base: datetime, count: int) -> list[str]:
        return [
            (base + timedelta(minutes=i - count)).strftime("%H:%M")
            for i in range(count)
        ]
