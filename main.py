from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI

MODEL_NAME = "text-embedding-3-small"
COVERAGE_THRESHOLD_080 = 0.80
COVERAGE_THRESHOLD_085 = 0.85
EVALUATION_THRESHOLDS = (
    0.70,
    0.75,
    COVERAGE_THRESHOLD_080,
    COVERAGE_THRESHOLD_085,
)
CACHE_PATH = Path("data/embedding_cache.json")
OUTPUTS_DIR = Path("outputs")
EVALUATION_METRICS_FILENAME = "evaluation_metrics.csv"
ALLOWED_EXPORT_FILES = {EVALUATION_METRICS_FILENAME}


class EmbeddingCache:
    """Simple JSON cache keyed by 'model::exact_text'."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = Lock()
        self._cache = self._load()

    def _load(self) -> dict[str, list[float]]:
        if not self.path.exists():
            return {}

        try:
            with self.path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
                if isinstance(payload, dict):
                    return payload
        except (json.JSONDecodeError, OSError):
            return {}

        return {}

    def get(self, key: str) -> list[float] | None:
        return self._cache.get(key)

    def set(self, key: str, value: list[float]) -> None:
        self._cache[key] = value

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(self._cache, file, ensure_ascii=False)
            temp_path.replace(self.path)


def parse_stories(file_bytes: bytes) -> list[str]:
    text = file_bytes.decode("utf-8-sig")
    # Trim each line and ignore empty rows so only valid stories remain.
    return [line.strip() for line in text.splitlines() if line.strip()]


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Environment variable OPENAI_API_KEY is missing.")
    return OpenAI(api_key=api_key)


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def build_evaluation_metrics(
    best_cosines: np.ndarray,
    similarities: np.ndarray,
) -> list[dict[str, Any]]:
    total_golden = int(best_cosines.shape[0])
    total_generated = int(similarities.shape[1])
    generated_max_cosines = (
        np.max(similarities, axis=0)
        if total_generated > 0
        else np.asarray([], dtype=np.float32)
    )

    metrics_rows: list[dict[str, Any]] = []
    for threshold in EVALUATION_THRESHOLDS:
        # Best-match policy for reference side:
        # TP_golden = count(max cosine per reference >= threshold)
        # FN = total_golden - TP_golden
        tp_golden = int(np.sum(best_cosines >= threshold))
        fn = total_golden - tp_golden

        # Any-match policy for generated side:
        # TP_generated = count(generated stories with any reference cosine >= threshold)
        # FP = total_generated - TP_generated
        tp_generated = int(np.sum(generated_max_cosines >= threshold))
        fp = total_generated - tp_generated

        # Recall = TP_golden / total_golden  (== coverage)
        recall = safe_ratio(tp_golden, total_golden)
        # Precision = TP_generated / total_generated
        precision = safe_ratio(tp_generated, total_generated)
        # F1 = 2 * (Precision * Recall) / (Precision + Recall)
        f1 = safe_ratio(2.0 * (precision * recall), precision + recall)

        metrics_rows.append(
            {
                "threshold": float(threshold),
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "tp": tp_golden,
                "fp": fp,
                "fn": fn,
                "total_golden": total_golden,
                "total_generated": total_generated,
            }
        )

    return metrics_rows


def get_embeddings(
    texts: list[str],
    client: OpenAI,
    cache: EmbeddingCache,
    model: str = MODEL_NAME,
) -> np.ndarray:
    unique_texts = list(dict.fromkeys(texts))
    vectors_by_text: dict[str, np.ndarray] = {}
    missing_texts: list[str] = []

    for text in unique_texts:
        cache_key = f"{model}::{text}"
        cached_vector = cache.get(cache_key)
        if cached_vector is None:
            missing_texts.append(text)
            continue
        vectors_by_text[text] = np.asarray(cached_vector, dtype=np.float32)

    for batch in chunked(missing_texts, 100):
        response = client.embeddings.create(model=model, input=batch)
        for source_text, item in zip(batch, response.data):
            vector = np.asarray(item.embedding, dtype=np.float32)
            vectors_by_text[source_text] = vector
            cache.set(f"{model}::{source_text}", vector.tolist())

    if missing_texts:
        cache.save()

    return np.vstack([vectors_by_text[text] for text in texts])


def compute_analysis(
    golden_stories: list[str],
    generated_stories: list[str],
    golden_embeddings: np.ndarray,
    generated_embeddings: np.ndarray,
) -> dict[str, Any]:
    golden_normalized = normalize_rows(golden_embeddings)
    generated_normalized = normalize_rows(generated_embeddings)
    similarities = golden_normalized @ generated_normalized.T

    # Coverage is based on each reference story's best (max) cosine match.
    best_cosines = (
        np.max(similarities, axis=1)
        if similarities.shape[1] > 0
        else np.zeros(len(golden_stories), dtype=np.float32)
    )

    golden_total = len(golden_stories)
    covered_080 = int(np.sum(best_cosines >= COVERAGE_THRESHOLD_080))
    covered_085 = int(np.sum(best_cosines >= COVERAGE_THRESHOLD_085))
    coverage_080 = safe_ratio(covered_080, golden_total) * 100
    coverage_085 = safe_ratio(covered_085, golden_total) * 100

    evaluation_metrics = build_evaluation_metrics(
        best_cosines=np.asarray(best_cosines, dtype=np.float32),
        similarities=similarities,
    )

    return {
        "summary": {
            "golden_count": len(golden_stories),
            "generated_count": len(generated_stories),
            "covered_080": covered_080,
            "covered_085": covered_085,
            "coverage_080": coverage_080,
            "coverage_085": coverage_085,
            "model_name": MODEL_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "evaluation_metrics": evaluation_metrics,
    }


def write_evaluation_metrics_csv(
    run_id: str,
    evaluation_metrics_rows: list[dict[str, Any]],
) -> None:
    run_dir = OUTPUTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    evaluation_metrics_path = run_dir / EVALUATION_METRICS_FILENAME
    with evaluation_metrics_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["threshold", "recall", "precision", "f1", "TP", "FP", "FN"])
        for row in evaluation_metrics_rows:
            writer.writerow(
                [
                    f"{row['threshold']:.2f}",
                    f"{row['recall']:.6f}",
                    f"{row['precision']:.6f}",
                    f"{row['f1']:.6f}",
                    row["tp"],
                    row["fp"],
                    row["fn"],
                ]
            )


app = FastAPI(title="Semantic Coverage Tool")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
cache = EmbeddingCache(CACHE_PATH)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "model_name": MODEL_NAME,
        },
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    golden_file: UploadFile | None = File(default=None),
    generated_file: UploadFile | None = File(default=None),
) -> HTMLResponse:
    context: dict[str, Any] = {
        "request": request,
        "model_name": MODEL_NAME,
    }

    try:
        if golden_file is None or generated_file is None:
            raise ValueError("Both reference.txt and generated.txt must be uploaded.")

        golden_bytes = await golden_file.read()
        generated_bytes = await generated_file.read()
        if not golden_bytes or not generated_bytes:
            raise ValueError("Uploaded files cannot be empty.")

        golden_stories = parse_stories(golden_bytes)
        generated_stories = parse_stories(generated_bytes)
        if not golden_stories:
            raise ValueError("reference.txt has no non-empty stories after trimming.")
        if not generated_stories:
            raise ValueError("generated.txt has no non-empty stories after trimming.")

        client = build_openai_client()
        golden_embeddings = get_embeddings(golden_stories, client, cache, MODEL_NAME)
        generated_embeddings = get_embeddings(
            generated_stories, client, cache, MODEL_NAME
        )

        analysis = compute_analysis(
            golden_stories=golden_stories,
            generated_stories=generated_stories,
            golden_embeddings=golden_embeddings,
            generated_embeddings=generated_embeddings,
        )

        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        write_evaluation_metrics_csv(
            run_id=run_id,
            evaluation_metrics_rows=analysis["evaluation_metrics"],
        )

        context.update({"analysis": analysis, "run_id": run_id})
    except UnicodeDecodeError:
        context["error"] = "Files must be valid UTF-8 text."
    except Exception as exc:  # noqa: BLE001
        context["error"] = str(exc)

    return templates.TemplateResponse("index.html", context)


@app.get("/download/{run_id}/{filename}")
async def download_csv(run_id: str, filename: str) -> FileResponse:
    if filename not in ALLOWED_EXPORT_FILES:
        raise HTTPException(status_code=404, detail="Unknown export file.")

    file_path = OUTPUTS_DIR / run_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export not found.")

    return FileResponse(
        path=file_path,
        media_type="text/csv; charset=utf-8",
        filename=filename,
    )
