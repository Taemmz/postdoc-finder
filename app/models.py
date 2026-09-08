from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RawVacancy(BaseModel):
    source: str
    title: str
    link: str
    snippet: str = ""
    query_type: Optional[str] = None


class PostdocRecord(BaseModel):
    institution: str
    department: Optional[str] = None
    research_focus: str
    country: Optional[str] = "Germany"
    city: Optional[str] = None
    link: str
    deadline: Optional[str] = None
    match_score: int = Field(ge=1, le=10)
    german_required: str
    position_type: str = "postdoc"
    employment_type: str = "full_time"
    status: str = "new"
    research_data: Dict[str, Any]


class SourceTelemetry(BaseModel):
    source: str
    pages: int = 1
    mode: str = "SINGLE_PAGE"  # "URL_PAGINATION", "API_OFFSET", "API_PAGE", "SINGLE_PAGE", "RSS_FEED", "SSR_SEARCH"
    completeness: str = "COMPLETE"  # "COMPLETE", "UNKNOWN", "FAILED"
    raw: int = 0
    eligible: int = 0
    historical: int = 0
    new: int = 0
    error: Optional[str] = None

