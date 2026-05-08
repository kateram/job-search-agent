from core.llm import client
from models.job import JobAnalysis
from rag.retriever import retrieve


SYSTEM_PROMPT = """You are an expert cover letter writer.
You write compelling, specific cover letters that sound human and personal.
Mirror the candidate's natural writing voice from their past letters.
Never use generic filler phrases like 'I am writing to express my interest'.
Return only the cover letter text, no JSON, no preamble.


Rules:
- Never use: "sits at the intersection of", "I am passionate about", "I am excited about", "resonates with me", "thrilled", "I am writing to express my interest"
- Never use the formula: "It's not X, it's Y" or "What matters is..." or "What appeals to me is..."
- Do not open by immediately listing skills or experiences — start with a brief, genuine statement of interest in the role
- Don't make grand claims about caring deeply about the company mission
- Only reference experiences explicitly present in the CV — no embellishment
- Be specific and concrete — vague claims must be backed by a real example
- Write like a competent, grounded person — confident but not arrogant
- Natural sentence variety — not all short, not all long
- The letter should feel like it was written by a real person, not assembled from parts
"""


async def run_cover_letter(job: JobAnalysis) -> str:
    """
    Write a tailored cover letter using the candidate's voice
    retrieved from past cover letters via RAG.
    """
    cv_chunks = retrieve(
        query=job.raw_text,
        collection_name="cv_docs",
        n_results=2
    )

    # Retrieve past cover letters if they exist, fall back gracefully
    try:
        letter_chunks = retrieve(
            query=job.raw_text,
            collection_name="cover_letters",
            n_results=2
        )
        voice_context = "\n\n".join(letter_chunks)
    except RuntimeError:
        voice_context = "No past cover letters available — use a confident, direct tone."

    cv_context = "\n\n".join(cv_chunks)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Write a tailored cover letter for this candidate and role.

Candidate CV (relevant sections):
{cv_context}

Past writing style/voice:
{voice_context}

Job details:
Company: {job.company_name}
Role: {job.role_title}
Required skills: {', '.join(job.required_skills)}
Responsibilities: {', '.join(job.responsibilities)}
Culture signals: {', '.join(job.culture_signals)}

Instructions:
- Open with one or two sentences expressing genuine but understated interest in the role — not gushing, not robotic
- Then naturally weave in 2-3 specific experiences from the CV that are directly relevant to this role
- Draw the connection between past work and this role 
- Close with a simple forward-looking sentence — no grand statements
- 3 paragraphs, moderate length
- No subject line, no sign-off, just the body
- Read it back and remove any sentence that sounds like it came from a template"""
            }
        ]
    )

    return response.content[0].text.strip()