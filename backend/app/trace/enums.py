"""Controlled vocabulary for trace spans."""

import enum


class SpanKind(str, enum.Enum):
    # One respondent message, from arriving to the reply being ready.
    turn = "turn"
    # One ask of the model for an action, including the nudged retry after a refusal.
    decision = "decision"
    # One HTTP call to one tier. Failed attempts are spans too: they are the failover cost.
    attempt = "attempt"
    # The engine's own check of the action the model chose, and what it concluded.
    validation = "validation"
