import json
from core.llm import client
from models.job import JobAnalysis
from models.application import ApplicationPackage


SYSTEM_PROMPT = """You are a critical reviewer helping a job candidate submit the strongest possible application.
You review CV tailoring notes, a cover letter, and a company brief together as a package.
You are honest and direct — if something is weak, say so specifically.
Always respond with valid JSON matching the requested schema exactly.
Do not include any text outside the JSON object."""


async def run_critic(
    job: JobAnalysis,
    cv_notes: list[str],
    cover_letter: str,
    company_brief: str,
) -> ApplicationPackage:
    """
    Review all agent outputs together, assign a fit score,
    and return a final ApplicationPackage.
    """
    review = await _review_outputs(job, cv_notes, cover_letter, company_brief)
    
    return ApplicationPackage(
        job=job,
        fit_score=review["fit_score"],
        cv_notes=review["refined_cv_notes"],
        cover_letter=review["refined_cover_letter"],
        company_brief=company_brief,
        quality_flags=review.get("quality_flags", []),
        status="To Apply",
    )


async def _review_outputs(
    job: JobAnalysis,
    cv_notes: list[str],
    cover_letter: str,
    company_brief: str,
) -> dict:
    """
    Send all outputs to Claude for cross-review and refinement.
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Review this job application package and return a refined version.

JOB:
Company: {job.company_name}
Role: {job.role_title}
Required skills: {', '.join(job.required_skills)}
Responsibilities: {', '.join(job.responsibilities)}
Red flags: {', '.join(job.red_flags)}

CV NOTES (from CV advisor agent):
{json.dumps(cv_notes, indent=2)}

COVER LETTER (from cover letter agent):
{cover_letter}

COMPANY BRIEF (from company intel agent):
{company_brief}

Review the package and return JSON in this exact format:
{{
    "fit_score": <integer 0-10 based on how well the candidate matches the role>,
    "fit_score_reasoning": "<one sentence explaining the score>",
    "refined_cv_notes": [<refined list of CV suggestions — remove generic ones, add any missing ones>],
    "refined_cover_letter": "<cover letter with any weak sentences improved — preserve the candidate's voice>",
    "quality_flags": [<list of any remaining weaknesses or inconsistencies — empty list if none>]
}}

Fit score guide:
0-3: Poor match, major skill gaps
4-6: Partial match, some relevant experience
7-8: Strong match, most requirements met
9-10: Exceptional match, exceeds requirements"""
            }
        ]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    return json.loads(raw)