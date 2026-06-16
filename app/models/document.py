from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class Document(BaseModel):
    title: str
    url: str

    source_name: str
    source_type: str

    author: str | None = None
    published_at: datetime | None = None

    summary: str = ""
    raw_text: str = ""
    

@dataclass
class TrendDocument:
    title: str
    url: str
    source_type: str
    published_at: Optional[datetime]
    summary: str
    embedding: list[float] | None = None

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()


@dataclass
class TrendCandidate:
    title: str
    mention_count: int
    source_types: list[str]
    keywords: list[str]
    embedding: list[float] | None
    documents: list[TrendDocument]
    scores: "TrendScores" = field(default_factory=lambda: TrendScores(0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0))
    time_series: list[dict] = field(default_factory=list)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def keys(self):
        return self.__dict__.keys()

    def items(self):
        return self.__dict__.items()


@dataclass
class TrendScores:
    mention_score: float
    diversity_score: float
    influence_score: float
    recency_score: float
    ai_importance_score: float
    embedding_score: float
    trend_momentum_score: float
    final_score: float