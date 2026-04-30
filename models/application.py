from pydantic import BaseModel, Field
from datetime import datetime, timezone
from models.job import JobAnalysis

class ApplicationPackage(BaseModel):
    job: JobAnalysis
    fit_score: int = Field(ge=0, le=10)
    cv_notes: list[str]               # bullet points - which sections to reword
    cover_letter: str
    company_brief: str                # 3-5 sentences of company intel
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "To Apply"          # what gets written to Airtable
