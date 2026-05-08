from core.llm import client
from models.job import JobAnalysis
from rag.retriever import retrieve


SYSTEM_PROMPT = """You are an expert CV/resume advisor. 
You help candidates tailor their CV to specific job postings.
Be specific and actionable — reference actual content from the CV DO NOT HALLUCINATE NEW SKILLS.
Return a JSON array of strings, each being one concrete suggestion.
Do not include any text outside the JSON array."""


async def run_cv_advisor(job: JobAnalysis) -> list[str]:
    """
    Compare job requirements against the candidate's CV
    and return specific tailoring suggestions.
    """
    relevant_chunks = retrieve(
        query=job.raw_text,
        collection_name="cv_docs",
        n_results=3
    )

    cv_context = "\n\n".join(relevant_chunks)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Based on this candidate's CV content and the job posting, 
suggest specific changes to tailor the CV for this role.

CV content (most relevant sections):
{cv_context}

Job posting:
Company: {job.company_name}
Role: {job.role_title}
Required skills: {', '.join(job.required_skills)}
Nice to have: {', '.join(job.nice_to_have_skills)}
Responsibilities: {', '.join(job.responsibilities)}

Return a JSON array of 4-6 specific, actionable suggestions like:
["Move the Zafin AI Observer bullet to the top of experience section", 
 "Add 'LLM agent' explicitly to skills section", ...]"""
            }
        ]
    )

    import json
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    return json.loads(raw)