# Job Search Agent

A five-agent AI pipeline that takes a job posting and produces a tailored application package — CV notes, cover letter, and company intelligence — with a browser dashboard for reviewing and iterating on every output.

Built with the Anthropic API, FastAPI, RAG over personal documents, and parallel async agent execution. No orchestration framework.

---

## Demo

![Dashboard](docs/screenshot.png)

> Paste a job URL or description → five agents run → review your package → click any sentence in the cover letter to select and rewrite it

---

## What it does

**Pipeline:** paste a job posting URL or raw text and five agents run autonomously:

1. **Job Analyst** — scrapes the posting, extracts required skills, responsibilities, culture signals, and red flags into a typed `JobAnalysis` model
2. **CV Advisor** — retrieves the most relevant sections of your CV via RAG and returns specific, actionable tailoring suggestions for this role
3. **Cover Letter Writer** — retrieves your writing style from past cover letters via RAG and drafts a tailored letter in your voice *(runs in parallel with agents 2 and 4)*
4. **Company Intel** — searches the web via Tavily for recent news, funding, Glassdoor ratings, and Reddit employee sentiment *(runs in parallel with agents 2 and 3)*
5. **Critic** — reviews all three outputs together for consistency, refines them, assigns a fit score (0–10), and flags weaknesses

Every run is saved locally to SQLite and accessible from the history view.

**Dashboard features:**
- URL or paste-text input toggle
- Live agent progress indicators
- Fit score with colour coding (green / amber / red)
- Job red flags surfaced from the posting
- Cover letter with **sentence-level selection and regeneration** — click any sentence, type feedback, rewrite just that part
- CV notes as an interactive checklist
- Company brief with employee sentiment from Reddit and Glassdoor
- Written sections tab — paste any application form question, generate an answer, iterate with feedback
- Full application history with status tracking (To Apply / Applied / Interviewing / Rejected / Offer)

---

## Architecture

```
Job URL / Raw Text
        |
        v
+-------------------------+
|   Agent 1               |
|   Job Analyst           |  <- scrape + LLM extraction -> JobAnalysis model
+-------------------------+
        |
        v
+--------------------------------------------------+
|  Agents 2, 3, 4 — asyncio.gather() parallel     |
|                                                  |
|  Agent 2: CV Advisor    (RAG over CV)            |
|  Agent 3: Cover Letter  (RAG over letters)       |
|  Agent 4: Company Intel (Tavily web search)      |
+--------------------------------------------------+
        |
        v
+-------------------------+
|   Agent 5               |
|   Critic                |  <- cross-reviews, scores, refines -> ApplicationPackage
+-------------------------+
        |
        v
  SQLite (local)    +    Browser dashboard
```

---

## Tech stack

- **LLM** — Anthropic Claude (Haiku for agents 1–4, Sonnet for agent 5 and cover letter iteration)
- **Agent framework** — raw Anthropic API + asyncio, no wrapper framework
- **RAG** — ChromaDB vector store, sentence-transformers (all-MiniLM-L6-v2), section-based CV chunking
- **Web search** — Tavily API
- **Web scraping** — httpx + BeautifulSoup with Tavily fallback for JS-rendered pages
- **API** — FastAPI
- **Storage** — SQLite via Python standard library
- **Validation** — Pydantic v2

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/kateram/job-search-agent.git
cd job-search-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
```

Fill in your keys:

```
ANTHROPIC_API_KEY=        # anthropic.com
TAVILY_API_KEY=           # tavily.com — free tier available
```

### 3. Add your CV

Add your CV as a `.txt` file to `data/cv/`. Optionally add past cover letters as `.txt` files to `data/cover_letters/` — these give the cover letter agent your writing voice.

Format your CV with all-caps section headers so the chunker splits it correctly:

```
EXPERIENCE: SOFTWARE ENGINEER — ACME CORP

- Built ...

EDUCATION

Bachelor of ...
```

Then ingest:

```bash
python -m rag.embedder
```

### 4. Run

```bash
python main.py
```

Open `http://localhost:8000`.

---

## Running tests

```bash
pytest tests/ -v
```

---

## Design decisions

**RAG over context stuffing** — CV and cover letter content is retrieved selectively per query rather than injected wholesale into every prompt. This reduces token cost, cuts noise, and means the cover letter agent sees only the CV sections most relevant to the specific role.

**Section-based chunking** — the CV is split on capitalised section headers rather than arbitrary word counts. This keeps each job and each project as an isolated, semantically coherent chunk, which improves retrieval precision compared to fixed-size splitting.

**Stored CV chunks for cover letter iteration** — the chunks used during the initial cover letter generation are stored alongside the application in SQLite. When you iterate on the cover letter, the same CV context is reused rather than re-retrieved, keeping the revision grounded in the same evidence as the original.

**Haiku for throughput, Sonnet for reasoning** — agents 1–4 use Claude Haiku for extraction, retrieval-augmented generation, and web synthesis. Agent 5 and the cover letter regeneration use Claude Sonnet where cross-document reasoning and quality of output matters most.

**Human-in-the-loop by default** — the pipeline produces a package for review, not a submission. The fit score and quality flags are signals to help prioritise, not automate the decision.