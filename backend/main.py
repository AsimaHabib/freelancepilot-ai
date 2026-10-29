from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import ai
import db
from analyzer import analyze_message
from proposal import build_proposal
from scope_creep import check_scope

app = FastAPI(title="FreelancePilot AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


class ClientMessage(BaseModel):
    message: str
    use_ai: bool = False


class ScopeCheck(BaseModel):
    agreement: str
    new_request: str
    use_ai: bool = False


class ProposalRequest(BaseModel):
    message: str
    freelancer_name: str = ""
    skills: str = ""
    use_ai: bool = False


def _short(text: str, size: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= size else text[: size - 1] + "…"


def _save(kind: str, title: str, input_data: dict, result: dict):
    # A saving problem should never stop the user from getting their result
    try:
        db.save_record(kind, title, input_data, result)
    except Exception as error:
        print("Could not save history:", error)


def _run_ai(task):
    # AI is an extra. If it fails, the rule-based result is still returned.
    try:
        return task()
    except ai.AIError as error:
        return {"error": str(error)}


@app.get("/")
def home():
    return {"message": "FreelancePilot AI is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(data: ClientMessage):
    result = analyze_message(data.message)
    if data.use_ai:
        result["ai"] = _run_ai(lambda: ai.analyze_with_ai(data.message, result))
    _save("analyze", _short(data.message), {"message": data.message}, result)
    return result


@app.post("/scope-check")
def scope_check(data: ScopeCheck):
    result = check_scope(data.agreement, data.new_request)
    if data.use_ai:
        result["ai"] = _run_ai(lambda: ai.scope_with_ai(data.agreement, data.new_request, result))
    _save(
        "scope",
        _short(data.new_request),
        {"agreement": data.agreement, "new_request": data.new_request},
        result,
    )
    return result


@app.post("/proposal")
def proposal(data: ProposalRequest):
    result = build_proposal(data.message, data.freelancer_name, data.skills)
    analysis = result.pop("_analysis")
    if data.use_ai:
        result["ai"] = _run_ai(
            lambda: ai.proposal_with_ai(data.message, data.freelancer_name, data.skills, analysis)
        )
    _save(
        "proposal",
        _short(data.message),
        {"message": data.message, "freelancer_name": data.freelancer_name, "skills": data.skills},
        result,
    )
    return result


@app.get("/ai/status")
def ai_status():
    return ai.status()


@app.get("/history")
def history():
    return db.list_records()


@app.get("/history/{record_id}")
def history_item(record_id: int):
    record = db.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    return record


@app.delete("/history/{record_id}")
def history_delete(record_id: int):
    if not db.delete_record(record_id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": record_id}