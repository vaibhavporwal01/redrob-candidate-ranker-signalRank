# Signalrank: Evidence-First Candidate Intelligence
**Redrob AI Hackathon Submission — Intelligent Candidate Discovery & Ranking Challenge**

Signalrank is a CPU-only, deterministic candidate ranking engine that evaluates 100,000+ candidates against a Senior AI Engineer JD, ranking them by career-history evidence rather than resume keyword density.

## Reproducing the submission

1. Install Python 3.12+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Place the organizer-provided `candidates.jsonl` at `data/candidates.jsonl` (not included in this repo — see "Data" below).
4. Run:
   ```bash
   python rank.py --candidates data/candidates.jsonl --out submission.csv
   ```
   This single command reproduces `submission.csv` from scratch — no manual edits, no hidden steps. There is no separate pre-computation step; embeddings and features are generated in-memory during this run.
5. Validate the output format:
   ```bash
   python validate_submission.py submission.csv
   ```

## Data

`data/candidates.jsonl` is the organizer-provided 100K candidate pool and is intentionally excluded from this repo (see `.gitignore`) since it isn't ours to redistribute. Drop your own copy at `data/candidates.jsonl` before running `rank.py`. Small reference files used for local testing (`sample_candidates.json`, `1k_sample.jsonl`, `candidate_schema.json`) are included.

## Compute constraints

Designed from the ground up to run within the hackathon's compute budget (5 min, 16GB RAM, CPU-only, no network during ranking):

- **No hosted LLM calls, no GPU, no network calls** during ranking. Semantic similarity uses a bespoke hashing-based pseudo-embedding (`redrob/retrieval/embeddings.py`) instead of a transformer model — fully deterministic, pure CPU/Python.
- Lexical (BM25) + hashed-embedding hybrid retrieval narrows the 100K pool before feature extraction and scoring.
- Verified against the official `validate_submission.py`: `Submission is valid.`

## Trap handling

- **Honeypots** (`redrob/features/honeypot.py`): flags implausible experience, reversed career timelines, "expert" proficiency with zero duration, excessive overlapping roles, and career-duration mismatches, applying a severity-based score multiplier.
- **JD-specific disqualifiers** (`redrob/features/disqualifiers.py`): encodes the JD's explicit "do NOT want" list — title-chasers (short average tenure + repeated senior titles), consulting-only career history, framework/LLM-wrapper-only experience without pre-LLM production depth, computer-vision/speech/robotics background without NLP/IR exposure, closed-source experience without external validation, and non-technical titles.
- **Behavioral signals**: recruiter response rate and recency-of-activity are folded into scoring as an availability multiplier, per the JD's explicit callout on "perfect-on-paper but unavailable" candidates.

## Reasoning column

Each ranked candidate's `reasoning` field is generated from that candidate's actual profile — quoting a real role description, matched skill groups, years of experience, and (where applicable) the specific disqualifier/honeypot flag that down-ranked them. Reasoning is not name-templated boilerplate.

## Local development / sandbox UI

To run the interactive dashboard used as the hosted sandbox:
```bash
uvicorn app.api:app --reload --port 7860
```
Then open `http://localhost:7860`.

## Docker

```bash
docker build -t signalrank .
docker run -p 7860:7860 signalrank
```

## Repository structure

```
hackathon/
├── rank.py                     # CLI entrypoint: candidates.jsonl -> submission.csv
├── main.py                     # Alternate entrypoint
├── requirements.txt            # Pinned dependencies
├── pyproject.toml              # Project metadata
├── Dockerfile                  # Container build for the hosted sandbox
├── submission.csv              # Final top-100 ranked submission
├── submission_metadata.yaml    # Team / AI-tool / compute declarations
├── validate_submission.py      # Official format validator (organizer-provided)
│
├── redrob/                     # Core ranking engine
│   ├── loader.py                #   Candidate JSONL loading
│   ├── normalization.py         #   Field extraction / normalization helpers
│   ├── jd.py                    #   Job description parsing + config
│   ├── scoring.py                #   Final composite score
│   ├── reasoning.py              #   Per-candidate reasoning text generation
│   ├── submission.py             #   CSV writer
│   ├── pipeline.py               #   End-to-end orchestration (rank_candidates / run)
│   ├── retrieval/                #   BM25 + hashed-embedding hybrid retrieval
│   └── features/                 #   Skill matching, career signals, disqualifiers, honeypots
│
├── app/                         # FastAPI backend + UI powering the hosted sandbox
├── config/                      # JD and scoring weight configs
├── data/                        # Schema + small sample files (full candidates.jsonl excluded)
└── tests/                       # Unit tests
```

## AI tools disclosure

Development used AI assistance (Claude, Gemini) for job-description analysis, pipeline scaffolding, formatting-constraint verification, and UI implementation, with all ranking logic, feature engineering, and disqualifier rules designed and reviewed as original engineering work. Full disclosure in `submission_metadata.yaml`.