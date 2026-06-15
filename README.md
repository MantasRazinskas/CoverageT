# Semantic Coverage Tool

A minimal, reproducible research application that measures how well a set of
**LLM-generated** user stories semantically covers a set of **expert-written
(reference)** user stories, using OpenAI sentence embeddings.

This repository accompanies a research paper on LLM-based user story generation.
It is published so that the reported coverage results can be independently
reproduced. The repository contains two reproducibility artifacts:

1. The **generation prompt** used to produce the user stories
   (`prompts/user_story_generation_prompt.md`).
2. The **evaluation tool** that computes semantic coverage and the
   recall / precision / F1 metrics reported in the paper (`main.py`).

## What it does

Given two plain-text files — one reference story per line, one generated story
per line — the tool:

1. Embeds every story with OpenAI `text-embedding-3-small`.
2. Computes cosine similarity for **all** reference-vs-generated pairs.
3. Takes, for each reference story, its best (maximum) cosine match.
4. Marks a reference story as **covered** when its best match `>= threshold`.
5. Reports, at thresholds `0.70`, `0.75`, `0.80`, `0.85`:
   - **Recall (coverage)** 
   - **Precision** 
   - **F1** 
   - Confusion counts `TP`, `FP`, `FN`
6. Exports the metrics table as `evaluation_metrics.csv`.

The scope is intentionally limited to results verification (coverage and the
recall / precision / F1 metrics), so the output maps directly onto the figures
reported in the paper.

## Input format

- One user story per line.
- Surrounding whitespace is trimmed; empty lines are ignored.
- UTF-8 is used throughout (important for Lithuanian text).

```
reference.txt   # expert-written stories, one per line
generated.txt   # LLM-generated stories, one per line
```

## Requirements

- Python 3.10+
- An `OPENAI_API_KEY` environment variable

## Run (Windows)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set OPENAI_API_KEY=your_key_here
uvicorn main:app --reload
```

Then open:

```
http://127.0.0.1:8000
```

## Usage

1. Open the web page.
2. Upload `reference.txt` and `generated.txt`.
3. Click **Analyze**.
4. Inspect the coverage summary and the per-threshold
   recall / precision / F1 table, and download `evaluation_metrics.csv`.

## Caching

Embeddings are cached locally by exact text + model in
`data/embedding_cache.json`, so repeated runs on unchanged stories do not call
the API again. CSV exports are written per run to `outputs/<run_id>/`.

## Project structure

```
main.py                                  # FastAPI app + coverage/metrics logic
templates/index.html                     # single-page UI
static/style.css                         # styling
prompts/user_story_generation_prompt.md  # exact LLM generation prompt
requirements.txt
README.md
```
