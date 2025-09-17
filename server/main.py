"""FastAPI application exposing DailyNews functionality."""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from dailynews.service import summarize_run

app = FastAPI(title="DailyNews API")

ALLOWED_ORIGINS = [
    "http://localhost:19006",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8081",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"http://127\\.0\\.0\\.1(:\\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Headline(BaseModel):
    title: str
    url: str
    source_domain: str
    seendate: str


class SummaryResponse(BaseModel):
    topics: List[str]
    hours: int
    region: Optional[str]
    language: Optional[str]
    fetched_count: int
    summary: str
    headlines: List[Headline]


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"message": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/summary", response_model=SummaryResponse)
def get_summary(
    *,
    topics: str = Query("finance,economy,politics", description="Comma separated topics"),
    hours: int = Query(8, ge=1, le=72),
    region: Optional[str] = Query(None, description="Optional region code"),
    language: Optional[str] = Query(None, description="Optional language code"),
    maxrecords: int = Query(75, ge=1, le=250),
) -> SummaryResponse:
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    if not topic_list:
        raise HTTPException(status_code=400, detail={"message": "At least one topic required"})

    result = summarize_run(
        topic_list,
        hours,
        region=region,
        language=language,
        maxrecords=maxrecords,
    )
    return SummaryResponse(**result)
