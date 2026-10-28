from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


from analyzer import analyze_message
from scope_creep import check_scope

app = FastAPI(title="FreelancePilot AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClientMessage(BaseModel):
    message: str


class ScopeCheck(BaseModel):
    agreement: str
    new_request: str


@app.get("/")
def home():
    return {"message": "FreelancePilot AI is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(data: ClientMessage):
    return analyze_message(data.message)


@app.post("/scope-check")
def scope_check(data: ScopeCheck):
    return check_scope(data.agreement, data.new_request)