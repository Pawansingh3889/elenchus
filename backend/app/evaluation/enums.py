import enum


class LabelVerdict(enum.StrEnum):
    """What a person decided about one recorded answer."""

    supported = "supported"
    invented = "invented"
    # Kept, not dropped: an answer somebody could not decide is a finding about the answer,
    # and it stays out of every rate rather than being forced into one side.
    unsure = "unsure"


class EvalRunStatus(enum.StrEnum):
    """Where one scenario run in an evaluation batch has got to."""

    queued = "queued"
    running = "running"
    completed = "completed"
    # Stopped because the batch reached its spend cap, before or during this scenario.
    capped = "capped"
    failed = "failed"
