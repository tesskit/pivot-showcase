# Skeleton of src/main.py: structure only. The implementation is private.
# Each stub has a one-line description of what it does.

from typing import List, Optional, Tuple, TypedDict

MODEL_DEFAULT = "claude-sonnet-4-6"       # Intake, Research, Narrative, Synthesizer
MODEL_FAST = "claude-haiku-4-5-20251001"  # Fact-Check, Application Coach, Courses Subagent, helper calls


class PivotState(TypedDict):
    """Shared state passed from agent to agent."""
    messages: List[dict]          # full conversation history
    user_input: str               # her most recent message
    profile: dict                 # what we know about her
    extracted_profile: dict       # fields the Python extractor accumulates across turns
    work_arrangement: str         # remote / hybrid / in-person / any
    research: dict                # Research Agent output
    verified_research: dict       # Fact-Check Agent output
    narrative: dict               # STAR story and resume bullets
    application_coach: dict       # resume bullets, cover letter opening, quick win
    live_jobs: str                # raw job listings with apply links
    courses: str                  # Courses Subagent output
    response: str                 # the final response she sees
    turn_count: int
    profile_complete: bool        # the gate that starts the pipeline
    excluded_employers: List[str]
    _pipeline_complete: bool      # set after the first full run, never cleared
    _is_resarch: bool             # set on a re-search
    _resarch_target: str          # new target for a re-search
    target_industry: str          # industry qualifier for the job search


# ---- Helpers ---------------------------------------------------------------

def _log_tokens(agent: str, model: str, input_tokens: int, output_tokens: int):
    """Record token usage for cost tracking."""
    ...

def load_file(*paths: str) -> str:
    """Load and join prompt and skill files from disk."""
    ...

def clean_job_query(raw_target: str, fallback_role: str) -> str:
    """Strip conversational text from a target role before searching."""
    ...

def clean_location(raw_location: str) -> str:
    """Strip conversational text from a location string."""
    ...

def should_search_remote(profile: dict) -> bool:
    """Decide whether to include remote roles in the search."""
    ...

def geocode_location(location_str: str) -> str:
    """Turn any location phrase into city and state using Nominatim."""
    ...

def normalize_job_title(raw_title: str) -> str:
    """Ask Claude for the standard title employers use ("maid" becomes "Housekeeper")."""
    ...

def infer_industry(target_title: str) -> Optional[str]:
    """Infer an industry qualifier from the target title."""
    ...

def extract_profile_fields(messages: list) -> dict:
    """Pull profile fields out of the conversation, accumulating across turns."""
    ...

def detect_job_search_intent(user_input: str) -> Tuple[bool, Optional[str]]:
    """Claude call that detects a new job search request and its target."""
    ...


# ---- RAG (pre-computed embeddings, numpy at runtime) -----------------------

def _load_embeddings_file():
    """Load the pre-computed embeddings file once into memory."""
    ...

def _keyword_query_vector(query: str, dim: int = 384):
    """Build a lightweight keyword-hash query vector (no model runs on the server)."""
    ...

def query_embeddings_file(profile: dict, top_k: int = 5) -> str:
    """Return the top matching source chunks by cosine similarity."""
    ...


# ---- Agents ----------------------------------------------------------------

def orchestrator(state: PivotState) -> PivotState:
    """Rule-based routing (no LLM call): Intake, Research, or Synthesizer only."""
    ...

def route_from_orchestrator(state: PivotState):
    """Return the next node chosen by the Orchestrator."""
    ...

def intake_agent(state: PivotState) -> PivotState:
    """Warm intake conversation that builds her profile and sets profile_complete."""
    ...

def courses_subagent(target_role: str) -> str:
    """Subagent: suggest 3 to 5 courses for the target role (runs in a background thread)."""
    ...

def research_agent(state: PivotState) -> PivotState:
    """Salary data, RAG context, and the live job waterfall (Indeed, LinkedIn, JSearch fallback, USAJobs)."""
    ...

def factcheck_agent(state: PivotState) -> PivotState:
    """Verify research and flag anything that cannot be confirmed."""
    ...

def run_narrative_and_coach(state: PivotState) -> PivotState:
    """Run the Narrative Agent and the Application Coach in parallel threads."""
    ...

def synthesizer_agent(state: PivotState) -> PivotState:
    """Her final voice: three short paragraphs, structured listings, one question."""
    ...

def fast_responder(state: PivotState) -> PivotState:
    """Phase 1 reply with jobs and courses, built without a Claude call."""
    ...

def route_from_intake(state: PivotState):
    """After Intake: go to Research if the profile just completed, otherwise end the turn."""
    ...


# ---- Graphs ----------------------------------------------------------------
# pivot        (full):   orchestrator -> intake -> research_agent -> factcheck -> narrative_and_coach -> synthesizer
# pivot_fast   (Phase 1): orchestrator -> intake -> research_agent -> factcheck -> fast_responder
# pivot_finish (Phase 2): narrative_and_coach -> synthesizer
