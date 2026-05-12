from core.llm import client
from models.job import JobAnalysis
from rag.retriever import retrieve


SYSTEM_PROMPT = """You are helping a job candidate answer written application questions.
You write clear, specific, honest answers that draw directly from the candidate's real experience.
Rules:
- Only reference experiences explicitly present in the CV context provided
- Never fabricate achievements or embellish
- Be direct and concrete — no filler phrases like 'I am passionate about' or 'I thrive in'
- Match the tone of the question — formal questions get formal answers, conversational ones get conversational answers
- Keep answers focused and appropriately concise — do not pad
- Return only the answer text, no preamble no markdown"""


async def generate_section(
    question: str,
    job: JobAnalysis,
    cv_chunks: list[str],
) -> str:
    """
    Generate an answer to a written application question.
    Uses stored CV chunks for context.
    """
    cv_context = "\n\n".join(cv_chunks)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Answer this application question for the candidate.

Candidate CV (relevant sections):
{cv_context}

Job details:
Company: {job.company_name}
Role: {job.role_title}
Required skills: {', '.join(job.required_skills)}

Application question:
{question}

Write a focused, honest answer that draws specifically from the candidate's experience above.
Length should match what the question warrants — shorter for simple questions, longer for complex ones."""
            }
        ]
    )

    return response.content[0].text.strip()


async def regenerate_section(
    question: str,
    current_answer: str,
    feedback: str,
    job: JobAnalysis,
    cv_chunks: list[str],
) -> str:
    """
    Revise an existing answer based on feedback.
    """
    cv_context = "\n\n".join(cv_chunks)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Revise this answer based on the feedback below.

Candidate CV context:
{cv_context}

Job details:
Company: {job.company_name}
Role: {job.role_title}

Question:
{question}

Current answer:
{current_answer}

Feedback: {feedback}

Return only the revised answer. Apply the feedback while keeping what works."""
            }
        ]
    )

    return response.content[0].text.strip()