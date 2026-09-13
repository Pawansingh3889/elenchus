"""What the embedding lens endpoints return."""

from uuid import UUID

from pydantic import BaseModel


class EmbeddingCost(BaseModel):
    """What building one report spent on embeddings, measured from the ledger.

    Texts are counted once each, by hash. A text the cache already held costs nothing and
    takes no time, so a repeat view of the same survey reads $0: that is the cache
    working, not a missing figure.
    """

    texts: int
    cached: int
    embedded: int
    calls: int
    prompt_tokens: int
    cost_usd: float
    # Calls that reported no usage: the cost is then a floor, not a total.
    unmetered_calls: int
    duration_ms: int


class MapPoint(BaseModel):
    answer_id: UUID
    run_id: UUID
    kind: str
    # What was recorded, in words: an option, "free text", "unanswerable", a rating.
    recorded: str
    # What the respondent actually typed that produced it.
    said: str
    x: float
    y: float
    neighbours: list[UUID]


class MapQuestion(BaseModel):
    position: int
    text: str
    answer_type: str
    points: list[MapPoint]


class AnswerMap(BaseModel):
    survey_title: str
    model: str
    # Answers left off the map because no respondent message preceded them.
    unplaced: int
    questions: list[MapQuestion]
    cost: EmbeddingCost


class Theme(BaseModel):
    size: int
    runs: int
    representative: str
    members: list[str]


class ThemeQuestion(BaseModel):
    position: int
    text: str
    texts: int
    themes: list[Theme]


class ThemeReport(BaseModel):
    survey_title: str
    model: str
    questions: list[ThemeQuestion]
    cost: EmbeddingCost


class DuplicatePair(BaseModel):
    first: str
    second: str
    first_run: UUID
    second_run: UUID
    similarity: float


class DuplicateReport(BaseModel):
    survey_title: str
    model: str
    threshold: float
    texts: int
    pairs: list[DuplicatePair]
    cost: EmbeddingCost


class GroundingJudged(BaseModel):
    said: str
    option: str
    options: list[str]
    language: str
    supported: bool
    word_supported: bool
    similarity: float
    # The chosen option's similarity less the best other option's: positive only when the
    # chosen option is the closest of its question's options to what was said.
    margin: float


class SweepPoint(BaseModel):
    margin: float
    false_accepts: int
    false_refusals: int


class GroundingReport(BaseModel):
    measured_at: str
    model: str
    pairs: int
    negatives: int
    word_false_accepts: int
    word_false_refusals: int
    recommended_margin: float | None
    at_recommended_false_accepts: int | None
    at_recommended_false_refusals: int | None
    # The gap the recommendation sits in: the closest refused wrong answer below it and the
    # lowest real answer it accepts above it. A narrow gap is a fragile number.
    highest_negative_margin: float | None
    lowest_positive_margin: float | None
    sweep: list[SweepPoint]
    judged: list[GroundingJudged]
    # The deployment's live settings, beside the measurement they should come from.
    semantic_enabled: bool
    configured_margin: float | None
