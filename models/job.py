from pydantic import BaseModel

class JobAnalysis(BaseModel):
    company_name: str
    role_title: str
    location: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    responsibilities: list[str]
    culture_signals: list[str]
    red_flags: list[str]
    raw_text: str           # full post