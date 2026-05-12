import json
from core.llm import client
from models.job import JobAnalysis
from rag.retriever import retrieve


SYSTEM_PROMPT = """You are helping a candidate write a natural, human-sounding cover letter.

Rules:
- Never use: "sits at the intersection of", "I am passionate about", "I am excited about", "resonates with me", "thrilled", "I am writing to express my interest"
- Never use the formula: "It's not X, it's Y" or "What matters is..." or "What appeals to me is..."
- Do not open by immediately listing skills or experiences — start with a brief, genuine statement of interest in the role
- Don't make grand claims about caring deeply about the company mission
- Only reference experiences explicitly present in the CV — no embellishment
- Be specific and concrete — vague claims must be backed by a real example
- Write like a competent, grounded person — confident but not arrogant
- Natural sentence variety — not all short, not all long
- The letter should feel like it was written by a real person, not assembled from parts"""


SENTENCE_SYSTEM_PROMPT = """You are editing specific sentences in a cover letter based on user feedback.
You will receive the full letter context and the sentences to rewrite.
Return ONLY a JSON array of the rewritten sentences in the same order.
Preserve the candidate's voice and maintain flow with surrounding sentences.
Do not include any text outside the JSON array."""


REGENERATE_SYSTEM_PROMPT = """You are rewriting a cover letter based on specific feedback.
You have access to the candidate's CV context and the original letter.
Apply the feedback while preserving what works.
Return only the revised cover letter text, no preamble."""


async def run_cover_letter(job: JobAnalysis) -> tuple[str, list[str]]:
    """
    Write a tailored cover letter.
    Returns a tuple of (cover_letter_text, cv_chunks_used).
    """
    cv_chunks = retrieve(
        query=job.raw_text,
        collection_name="cv_docs",
        n_results=3
    )

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
                "content": f"""Write a cover letter for this candidate applying to this role.

Candidate CV (relevant sections):
{cv_context}

Past writing style/voice:
{voice_context}

Job details:
Company: {job.company_name}
Role: {job.role_title}
Required skills: {', '.join(job.required_skills)}
Culture signals: {', '.join(job.culture_signals)}

Write a 3 paragraph cover letter. Be specific about the company and role.
Reference real experience from the CV. Match the candidate's voice."""
            }
        ]
    )

    return response.content[0].text.strip(), cv_chunks


async def regenerate_sentences(
    full_letter: str,
    selected_indices: list[int],
    feedback: str,
    job: JobAnalysis,
    cv_chunks: list[str],
) -> str:
    """
    Rewrite only the selected sentences in the letter based on feedback.
    Returns the full letter with selected sentences replaced.
    """
    sentences = _split_sentences(full_letter)
    selected_sentences = [sentences[i] for i in selected_indices if i < len(sentences)]
    cv_context = "\n\n".join(cv_chunks)

    # Build surrounding context so the agent understands the flow
    before = sentences[max(0, min(selected_indices) - 2): min(selected_indices)]
    after = sentences[max(selected_indices) + 1: max(selected_indices) + 3]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SENTENCE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Rewrite these sentences based on the feedback below.

Candidate CV context:
{cv_context}

Full letter for context:
{full_letter}

Sentences before the selection (for flow):
{' '.join(before)}

Sentences to rewrite:
{json.dumps(selected_sentences)}

Sentences after the selection (for flow):
{' '.join(after)}

Feedback: {feedback}

Return a JSON array of the rewritten sentences, one per original sentence selected.
Maintain the candidate's voice and ensure smooth flow with surrounding text."""
            }
        ]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    rewritten = json.loads(raw)

    # Splice rewritten sentences back in
    for i, idx in enumerate(selected_indices):
        if idx < len(sentences) and i < len(rewritten):
            sentences[idx] = rewritten[i]

    return " ".join(sentences)


async def regenerate_full_letter(
    current_letter: str,
    feedback: str,
    job: JobAnalysis,
    cv_chunks: list[str],
) -> str:
    """
    Rewrite the entire cover letter based on free-form feedback.
    Returns the revised letter text.
    """
    cv_context = "\n\n".join(cv_chunks)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=REGENERATE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Revise this cover letter based on the feedback below.

Candidate CV context:
{cv_context}

Job details:
Company: {job.company_name}
Role: {job.role_title}
Required skills: {', '.join(job.required_skills)}

Current letter:
{current_letter}

Feedback: {feedback}

Return only the revised letter. Preserve what works, fix what the feedback addresses.
Keep the same voice and length unless the feedback says otherwise."""
            }
        ]
    )

    return response.content[0].text.strip()


def _split_sentences(text: str) -> list[str]:
    """
    Split cover letter text into sentences.
    Preserves paragraph breaks as sentence boundaries.
    """
    import re
    # Split on sentence endings but keep the punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]