# Skeleton of src/api.py: structure only. The implementation is private.
# FastAPI wrapper around the LangGraph pipelines. Each stub has a one-line description.

from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Message, token, session id, and the browser's copy of session state."""
    ...

class ChatResponse(BaseModel):
    """Reply text, session id, session state, and packet-ready flags."""
    ...

class EmailRequest(BaseModel):
    """Address to send the career packet to, plus session id and state."""
    ...


async def lifespan(app: FastAPI):
    """On startup: pre-warm embeddings, initialize the database, purge expired sessions, start the cleanup thread."""
    ...

app = FastAPI()


def check_token(token: Optional[str]) -> None:
    """Reject requests that do not carry the preview token."""
    ...


@app.api_route("/", methods=["GET", "HEAD"])
def health():
    """Health check used by UptimeRobot."""
    ...

@app.post("/chat")
async def chat(request: ChatRequest):
    """Run the full pipeline in one request."""
    ...

@app.post("/chat/fast")
async def chat_fast(request: ChatRequest):
    """Phase 1: Intake, Research, Fact-Check. Returns jobs and courses first."""
    ...

@app.post("/chat/finish")
async def chat_finish(request: ChatRequest):
    """Phase 2: Narrative, Application Coach, Synthesizer. Activates the email button."""
    ...

@app.post("/session/load")
async def load_session(request):
    """Restore a returning session (404 when nothing is stored, so the browser copy is used)."""
    ...

@app.api_route("/cleanup", methods=["GET", "POST", "HEAD"])
async def cleanup():
    """Delete expired sessions."""
    ...

@app.post("/ping")
async def ping(request):
    """Reset the inactivity clock when she clicks "Keep it going"."""
    ...

@app.delete("/session")
async def end_session(request):
    """Delete a session when she ends it."""
    ...

@app.post("/email")
async def send_email(request: EmailRequest):
    """Build the HTML and plain text career packet and send it with Resend."""
    ...


def check_admin(request: Request):
    """Guard for the admin dashboard routes."""
    ...

# /admin/* routes (cost, usage, sessions, services dashboard) are omitted from this skeleton.
