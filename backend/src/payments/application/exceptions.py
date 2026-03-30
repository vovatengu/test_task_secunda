from __future__ import annotations


class IdempotencyKeyConflictError(Exception):
    """Client reused Idempotency-Key with a different request body than the original."""
