import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.pipeline import run_pipeline
from tools.storage import get_all_applications, get_application, update_status
from agents.cover_letter import regenerate_sentences, regenerate_full_letter, _split_sentences
from agents.job_analyst import run_job_analyst
from agents.written_sections import generate_section, regenerate_section


router = APIRouter()


class PipelineRequest(BaseModel):
    url: str = None
    raw_text: str = None


class StatusUpdate(BaseModel):
    status: str

class RegenerateRequest(BaseModel):
    application_id: int
    feedback: str
    selected_indices: list[int] = []   
    current_letter: str

class SectionRequest(BaseModel):
    application_id: int
    question: str


class SectionRegenerateRequest(BaseModel):
    application_id: int
    question: str
    current_answer: str
    feedback: str

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

@router.post("/regenerate-cover-letter")
async def regenerate_cover_letter(request: RegenerateRequest):
    try:
        data = get_application(request.application_id)
        if not data:
            return JSONResponse(status_code=404, content={"error": "Application not found"})

        # Reconstruct job from stored data
        from models.job import JobAnalysis
        job = JobAnalysis(
            company_name=data["company"],
            role_title=data["role"],
            location=data.get("location", ""),
            required_skills=data.get("required_skills", []),
            nice_to_have_skills=[],
            responsibilities=[],
            culture_signals=[],
            red_flags=data.get("red_flags", []),
            raw_text=data.get("raw_text", ""),
        )

        cv_chunks = data.get("cv_chunks", [])

        if request.selected_indices:
            new_letter = await regenerate_sentences(
                full_letter=request.current_letter,
                selected_indices=request.selected_indices,
                feedback=request.feedback,
                job=job,
                cv_chunks=cv_chunks,
            )
        else:
            new_letter = await regenerate_full_letter(
                current_letter=request.current_letter,
                feedback=request.feedback,
                job=job,
                cv_chunks=cv_chunks,
            )

        # Save updated letter to db
        from tools.storage import _get_conn
        conn = _get_conn()
        conn.execute(
            "UPDATE applications SET cover_letter = ? WHERE id = ?",
            (new_letter, request.application_id)
        )
        conn.commit()
        conn.close()

        return JSONResponse(content={
            "cover_letter": new_letter,
            "sentences": _split_sentences(new_letter)
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/generate-section")
async def generate_section_route(request: SectionRequest):
    try:
        data = get_application(request.application_id)
        if not data:
            return JSONResponse(status_code=404, content={"error": "Application not found"})

        from models.job import JobAnalysis
        job = JobAnalysis(
            company_name=data["company"],
            role_title=data["role"],
            location=data.get("location", ""),
            required_skills=data.get("required_skills", []),
            nice_to_have_skills=[],
            responsibilities=[],
            culture_signals=[],
            red_flags=data.get("red_flags", []),
            raw_text=data.get("raw_text", ""),
        )

        cv_chunks = data.get("cv_chunks", [])
        answer = await generate_section(
            question=request.question,
            job=job,
            cv_chunks=cv_chunks,
        )

        return JSONResponse(content={"answer": answer})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/regenerate-section")
async def regenerate_section_route(request: SectionRegenerateRequest):
    try:
        data = get_application(request.application_id)
        if not data:
            return JSONResponse(status_code=404, content={"error": "Application not found"})

        from models.job import JobAnalysis
        job = JobAnalysis(
            company_name=data["company"],
            role_title=data["role"],
            location=data.get("location", ""),
            required_skills=data.get("required_skills", []),
            nice_to_have_skills=[],
            responsibilities=[],
            culture_signals=[],
            red_flags=data.get("red_flags", []),
            raw_text=data.get("raw_text", ""),
        )

        cv_chunks = data.get("cv_chunks", [])
        answer = await regenerate_section(
            question=request.question,
            current_answer=request.current_answer,
            feedback=request.feedback,
            job=job,
            cv_chunks=cv_chunks,
        )

        return JSONResponse(content={"answer": answer})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})