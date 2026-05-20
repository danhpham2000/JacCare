from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import json
import os
import sys

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import sqlite3
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.auth_store import (
    create_session,
    create_user,
    delete_session,
    get_profile,
    init_db,
    list_route_runs,
    save_profile,
    save_route_run,
    user_for_token,
    authenticate_user,
)
from services.care_engine import (
    build_call_script,
    clinic_scores,
    generate_plan,
    graph_data,
    normalize_intake,
    safety_check,
    translate_text,
)
from services.firecrawl_service import search_live_eligibility
from services.neo4j_store import graph_store

load_dotenv(BASE_DIR / ".env")


class IntakeRequest(BaseModel):
    zip_code: str = ""
    insurance_status: str = "uninsured"
    insurance_provider: str = ""
    insurance_plan: str = ""
    member_id: str = ""
    budget: int = Field(default=50, ge=0, le=1000)
    language: str = "English"
    transport_mode: str = "public_transit"
    care_need: str = ""
    urgency: str = "today"
    household: str = ""


class TranslateRequest(BaseModel):
    text: str
    language: str = "Spanish"


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class SessionResponse(BaseModel):
    token: str
    user: dict[str, Any]


app = FastAPI(
    title="JacCareRoute",
    description="Healthcare access navigator",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS), name="frontend-assets")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.on_event("shutdown")
def shutdown() -> None:
    graph_store.close()


def get_token(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    return authorization.split(" ", 1)[1].strip()


def current_user(token: str = Depends(get_token)) -> dict[str, Any]:
    user = user_for_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    return user


def intake_response_payload(user: dict[str, Any], intake: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_intake(intake)
    normalized["user_id"] = f"user_{user['id']}"
    return normalized


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "careroute-ai", "neo4j": graph_store.health()}


@app.get("/api/public-config")
def public_config() -> dict[str, Any]:
    return {
        "mapkit_token": os.getenv("MAPKIT_JS_TOKEN") or os.getenv("VITE_MAPKIT_TOKEN"),
        "neo4j": graph_store.health(),
    }


@app.post("/api/auth/register", response_model=SessionResponse)
def register(payload: RegisterRequest) -> dict[str, Any]:
    try:
        user = create_user(payload.full_name, payload.email, payload.password)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists") from exc
    token = create_session(int(user["id"]))
    return {"token": token, "user": {**user, "profile": get_profile(int(user["id"]))}}


@app.post("/api/auth/login", response_model=SessionResponse)
def login(payload: LoginRequest) -> dict[str, Any]:
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_session(int(user["id"]))
    return {"token": token, "user": {**user, "profile": get_profile(int(user["id"]))}}


@app.post("/api/auth/logout")
def logout(token: str = Depends(get_token)) -> dict[str, bool]:
    delete_session(token)
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {**user, "profile": get_profile(int(user["id"]))}


@app.get("/api/profile")
def profile(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return get_profile(int(user["id"]))


@app.put("/api/profile")
def update_profile(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    normalized = intake_response_payload(user, payload.model_dump())
    return save_profile(int(user["id"]), normalized)


@app.get("/api/history")
def history(user: dict[str, Any] = Depends(current_user)) -> list[dict[str, Any]]:
    return list_route_runs(int(user["id"]))


@app.post("/api/intake")
def intake(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    profile_data = intake_response_payload(user, payload.model_dump())
    save_profile(int(user["id"]), profile_data)
    return {"user_id": profile_data["user_id"], "status": "created"}


@app.post("/api/safety-check")
def safety(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return safety_check(intake_response_payload(user, payload.model_dump()))


@app.post("/api/match-care")
def match_care(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    profile_data = intake_response_payload(user, payload.model_dump())
    return {"top_options": clinic_scores(profile_data)[:5]}


@app.post("/api/generate-plan")
def plan(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    profile_data = intake_response_payload(user, payload.model_dump())
    return generate_plan(profile_data)


@app.post("/api/generate-call-script")
def call_script(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    profile_data = intake_response_payload(user, payload.model_dump())
    ranked = clinic_scores(profile_data)
    return {"script": build_call_script(profile_data, ranked[0] if ranked else None, profile_data["language"])}


@app.post("/api/translate")
def translate(payload: TranslateRequest, _: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    return {"language": payload.language, "translated_text": translate_text(payload.text, payload.language)}


@app.post("/api/graph")
def graph_for_payload(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return graph_data(intake_response_payload(user, payload.model_dump()))


@app.get("/api/graph/{run_id}")
def graph_for_run(run_id: int, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    record = graph_store.fetch_route_graph(run_id)
    if record:
        return record

    runs = {item["id"]: item for item in list_route_runs(int(user["id"]))}
    if run_id not in runs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route graph not found")
    payload = json.loads(runs[run_id]["payload_json"])
    return graph_data(payload)


@app.post("/api/run-care-route")
def run_care_route(payload: IntakeRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    profile_data = intake_response_payload(user, payload.model_dump())
    save_profile(int(user["id"]), profile_data)
    plan_result = generate_plan(profile_data)
    live_eligibility = search_live_eligibility(profile_data)
    graph = graph_data(profile_data)
    route_run_id = save_route_run(
        int(user["id"]),
        json.dumps(profile_data),
        json.dumps({**plan_result, "graph": graph, "live_eligibility": live_eligibility}),
        plan_result["summary"],
        plan_result["recommended_clinic"]["name"] if plan_result.get("recommended_clinic") else None,
        plan_result["backup_clinic"]["name"] if plan_result.get("backup_clinic") else None,
    )
    try:
        graph_store.sync_route_graph(route_run_id, user, profile_data, plan_result, graph)
    except Exception:
        # Route planning should still succeed if Aura is unavailable.
        pass
    persisted_graph = graph_store.fetch_route_graph(route_run_id) or graph
    return {**plan_result, "graph": persisted_graph, "live_eligibility": live_eligibility, "run_id": route_run_id}


@app.get("/")
def frontend_index() -> FileResponse:
    if FRONTEND_DIST.exists():
        return FileResponse(
            FRONTEND_DIST / "index.html",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend build not found")


@app.get("/{full_path:path}")
def frontend_spa(full_path: str) -> FileResponse:
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if FRONTEND_DIST.exists():
        return FileResponse(
            FRONTEND_DIST / "index.html",
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend build not found")
