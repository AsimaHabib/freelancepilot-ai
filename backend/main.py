from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import ai
import auth
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
limiter = auth.LoginLimiter()


# ---------- request shapes ----------

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


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


# ---------- helpers ----------

def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Every private endpoint uses this. No valid token means no access."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please sign in.")
    user = db.get_session_user(auth.hash_token(authorization[7:].strip()))
    if user is None:
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
    return user


def _short(text: str, size: int = 90) -> str:
    text = " ".join(text.split())
    return text if len(text) <= size else text[: size - 1] + "…"


def _save(user_id: int, kind: str, title: str, input_data: dict, result: dict):
    # A saving problem should never stop the user from getting their result
    try:
        db.save_record(user_id, kind, title, input_data, result)
    except Exception as error:
        print("Could not save history:", error)


def _run_ai(task):
    # AI is an extra. If it fails, the rule-based result is still returned.
    try:
        return task()
    except ai.AIError as error:
        return {"error": str(error)}


def _session_for(user: dict) -> dict:
    token = auth.new_token()
    db.create_session(user["id"], auth.hash_token(token))
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    }


# ---------- public ----------

@app.get("/")
def home():
    return {"message": "FreelancePilot AI is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------- accounts ----------

@app.post("/auth/register")
def register(data: RegisterRequest):
    name = data.name.strip()
    email = data.email.strip().lower()
    if not 1 <= len(name) <= 80:
        raise HTTPException(status_code=400, detail="Please enter your name.")
    if len(email) > 254 or not auth.EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if not 8 <= len(data.password) <= 200:
        raise HTTPException(status_code=400, detail="Password must be 8 to 200 characters long.")

    try:
        user_id = db.create_user(email, name, auth.hash_password(data.password))
    except ValueError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    return _session_for({"id": user_id, "name": name, "email": email})


@app.post("/auth/login")
def login(data: LoginRequest, request: Request):
    email = data.email.strip().lower()
    key = f"{request.client.host if request.client else 'unknown'}:{email}"
    if limiter.blocked(key):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")

    user = db.get_user_by_email(email)
    stored = user["password_hash"] if user else auth.DUMMY_HASH
    password_ok = auth.verify_password(data.password[:200], stored)
    if user is None or not password_ok:
        limiter.fail(key)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    limiter.reset(key)
    return _session_for(user)


@app.get("/auth/me")
def me(user: dict = Depends(current_user)):
    return user


@app.post("/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.lower().startswith("bearer "):
        db.delete_session(auth.hash_token(authorization[7:].strip()))
    return {"signed_out": True}


# ---------- private features ----------

@app.post("/analyze")
def analyze(data: ClientMessage, user: dict = Depends(current_user)):
    result = analyze_message(data.message)
    if data.use_ai:
        result["ai"] = _run_ai(lambda: ai.analyze_with_ai(data.message, result))
    _save(user["id"], "analyze", _short(data.message), {"message": data.message}, result)
    return result


@app.post("/scope-check")
def scope_check(data: ScopeCheck, user: dict = Depends(current_user)):
    result = check_scope(data.agreement, data.new_request)
    if data.use_ai:
        result["ai"] = _run_ai(lambda: ai.scope_with_ai(data.agreement, data.new_request, result))
    _save(
        user["id"],
        "scope",
        _short(data.new_request),
        {"agreement": data.agreement, "new_request": data.new_request},
        result,
    )
    return result


@app.post("/proposal")
def proposal(data: ProposalRequest, user: dict = Depends(current_user)):
    result = build_proposal(data.message, data.freelancer_name, data.skills)
    analysis = result.pop("_analysis")
    if data.use_ai:
        result["ai"] = _run_ai(
            lambda: ai.proposal_with_ai(data.message, data.freelancer_name, data.skills, analysis)
        )
    _save(
        user["id"],
        "proposal",
        _short(data.message),
        {"message": data.message, "freelancer_name": data.freelancer_name, "skills": data.skills},
        result,
    )
    return result


@app.get("/ai/status")
def ai_status(user: dict = Depends(current_user)):
    return ai.status()


@app.get("/history")
def history(user: dict = Depends(current_user)):
    return db.list_records(user["id"])


@app.get("/history/{record_id}")
def history_item(record_id: int, user: dict = Depends(current_user)):
    record = db.get_record(user["id"], record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    return record


@app.delete("/history/{record_id}")
def history_delete(record_id: int, user: dict = Depends(current_user)):
    if not db.delete_record(user["id"], record_id):
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": record_id}