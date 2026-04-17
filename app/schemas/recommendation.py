from datetime import datetime

from pydantic import BaseModel


class RecommendationOut(BaseModel):
    event_id: int
    event_title: str
    category: str
    show_id: int
    show_start_at: datetime
    reason: str


class RecommendationResponse(BaseModel):
    items: list[RecommendationOut]
