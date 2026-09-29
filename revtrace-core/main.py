import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    init_db,
    create_account,
    get_account,
    get_accounts,
    update_account_stage,
    create_event,
    get_account_events,
)

from hindsight_service import (
    retain_journey_event,
    recall_account_journey,
)


app = FastAPI(
    title="RevTrace Core API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()


class AccountCreate(BaseModel):
    company: str
    contact_name: str | None = None
    industry: str | None = None
    role: str | None = None


class JourneyEventCreate(BaseModel):
    account_id: str
    opportunity_id: str | None = None
    agent: str
    event_type: str
    stage: str
    summary: str
    payload: dict = {}


class StageUpdate(BaseModel):
    stage: str
    current_agent: str
    opportunity_id: str | None = None


@app.get("/")
def root():
    return {
        "message": "RevTrace Core API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "RevTrace Core",
        "shared_memory": "Hindsight Cloud",
        "workflow_database": "SQLite",
    }


@app.post("/accounts")
def new_account(data: AccountCreate):
    account_id = "ACC-" + uuid.uuid4().hex[:6].upper()

    account = {
        "account_id": account_id,
        "opportunity_id": None,
        "company": data.company,
        "contact_name": data.contact_name,
        "industry": data.industry,
        "role": data.role,
        "stage": "NEW_PROSPECT",
        "current_agent": "PROSPECTING",
    }

    create_account(account)

    return get_account(account_id)


@app.get("/accounts")
def list_accounts():
    return {
        "accounts": get_accounts()
    }


@app.get("/accounts/{account_id}")
def account_details(account_id: str):
    account = get_account(account_id)

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    events = get_account_events(account_id)

    return {
        "account": account,
        "events": events,
    }


@app.post("/accounts/{account_id}/stage")
def change_stage(
    account_id: str,
    data: StageUpdate,
):
    account = get_account(account_id)

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    update_account_stage(
        account_id=account_id,
        stage=data.stage,
        current_agent=data.current_agent,
        opportunity_id=data.opportunity_id,
    )

    return get_account(account_id)


@app.post("/events")
def add_event(data: JourneyEventCreate):
    account = get_account(
        data.account_id
    )

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    event_id = (
        "EVT-"
        + uuid.uuid4().hex[:8].upper()
    )

    event = {
        "event_id": event_id,
        "account_id": data.account_id,
        "opportunity_id":
            data.opportunity_id,
        "agent": data.agent,
        "event_type":
            data.event_type,
        "stage": data.stage,
        "summary": data.summary,
        "payload": data.payload,
    }

    create_event(event)

    retain_journey_event(
        account_id=data.account_id,
        opportunity_id=
            data.opportunity_id,
        company=account["company"],
        agent=data.agent,
        stage=data.stage,
        event_type=data.event_type,
        summary=data.summary,
        payload=data.payload,
    )

    update_account_stage(
        account_id=data.account_id,
        stage=data.stage,
        current_agent=data.agent,
        opportunity_id=
            data.opportunity_id,
    )

    return {
        "status": "EVENT_SAVED",
        "event": event,
        "account": get_account(
            data.account_id
        ),
        "memory": {
            "provider":
                "Hindsight Cloud",
            "bank":
                "revtrace-shared-memory",
            "operation":
                "RETAIN",
        },
    }


@app.get(
    "/accounts/{account_id}/memory"
)
def account_memory(account_id: str):
    account = get_account(account_id)

    if not account:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    memories = recall_account_journey(
        account_id=account_id,
        company=account["company"],
    )

    return {
        "account_id": account_id,
        "company": account["company"],
        "memory_provider":
            "Hindsight Cloud",
        "memories": memories,
    }