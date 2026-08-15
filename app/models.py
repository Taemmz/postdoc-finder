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
    research_focus: str
    link: str
    deadline: Optional[str] = None
    match_score: int = Field(ge=1, le=10)
    german_required: str
    position_type: str = "postdoc"
    employment_type: str = "full_time"
    status: str = "new"
    research_data: Dict[str, Any]
