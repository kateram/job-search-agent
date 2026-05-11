import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.pipeline import run_pipeline

router = APIRouter()


class PipelineRequest(BaseModel):
    url: str = None
    raw_text: str = None


@router.post("/run")
async def run(request: PipelineRequest):
    try:
        package = await run_pipeline(
            url=request.url or None,
            raw_text=request.raw_text or None,
        )
        return JSONResponse(content={
            "company_name": package.job.company_name,
            "role_title": package.job.role_title,
            "location": package.job.location,
            "fit_score": package.fit_score,
            "cv_notes": package.cv_notes,
            "cover_letter": package.cover_letter,
            "company_brief": package.company_brief,
            "quality_flags": package.quality_flags,
            "required_skills": package.job.required_skills,
            "red_flags": package.job.red_flags,
            "status": package.status,
        })
    except Exception as e:
        traceback.print_exc()    # ← prints full stack trace to terminal
        return JSONResponse(status_code=500, content={"error": str(e)})