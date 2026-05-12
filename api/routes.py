import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.pipeline import run_pipeline
from tools.storage import get_all_applications, get_application, update_status

router = APIRouter()


class PipelineRequest(BaseModel):
    url: str = None
    raw_text: str = None


class StatusUpdate(BaseModel):
    status: str


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
            "red_flags": package.job.red_flags,
            "required_skills": package.job.required_skills,
            "status": package.status,
        })
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/applications")
async def list_applications():
    try:
        return JSONResponse(content=get_all_applications())
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/applications/{app_id}")
async def get_one(app_id: int):
    data = get_application(app_id)
    if not data:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return JSONResponse(content=data)


@router.patch("/applications/{app_id}/status")
async def patch_status(app_id: int, body: StatusUpdate):
    updated = update_status(app_id, body.status)
    if not updated:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return JSONResponse(content={"ok": True})