import uuid

from fastapi import (
    FastAPI,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from pydantic import BaseModel


from backend.database import (
    init_db,
    insert_prospect,
    get_prospect,
    get_all_prospects,
    update_analysis,
    update_message,
    update_outcome,
    schedule_meeting,
    complete_meeting,
)


from backend.hindsight_service import (
    recall_similar_prospects,
    filter_comparable_prospects,
    retain_prospect_memory,
    client as hindsight_client,
)


from backend.analytics import (
    analyze_prospects,
)


from backend.llm_service import (
    generate_outreach_message,
)


# =======================================================
# REVTRACE CORE INTEGRATION
# =======================================================

from backend.core_service import (
    create_core_account,
    send_core_event,
    update_core_stage,
)


# =======================================================
# APP
# =======================================================

app = FastAPI(
    title="RevTrace Prospecting Agent",
    version="1.1.0",
)


# -------------------------------------------------------
# CORS
# -------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()


# =======================================================
# MODELS
# =======================================================

class ProspectCreate(BaseModel):
    name: str
    company: str
    industry: str
    role: str
    company_size: str
    pain_point: str


class OutcomeUpdate(BaseModel):
    outcome: str


class MeetingCreate(BaseModel):
    meeting_date: str
    meeting_time: str


# =======================================================
# HELPERS
# =======================================================

def get_prospect_or_404(
    prospect_id: str
):
    prospect = get_prospect(
        prospect_id
    )

    if not prospect:
        raise HTTPException(
            status_code=404,
            detail="Prospect not found",
        )

    return prospect


def safe_core_event(
    prospect,
    event_type,
    stage,
    summary,
    payload=None,
    opportunity_id=None,
):
    """
    Send journey event to RevTrace Core.

    We do not fail the local Prospecting workflow
    if Core temporarily fails after prospect creation.
    """

    account_id = prospect.get(
        "account_id"
    )

    if not account_id:
        print(
            "Core sync skipped: "
            "prospect has no account_id"
        )

        return None

    try:
        return send_core_event(
            account_id=account_id,
            opportunity_id=opportunity_id,
            event_type=event_type,
            stage=stage,
            summary=summary,
            payload=payload or {},
        )

    except Exception as exc:
        print(
            "RevTrace Core event warning:",
            exc,
        )

        return None


# =======================================================
# BASIC ROUTES
# =======================================================

@app.get("/")
def root():
    return {
        "message":
            "RevTrace Prospecting Agent is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",

        "service":
            "RevTrace Prospecting Agent",

        "memory_provider":
            "Hindsight Cloud",

        "generation_provider":
            "Groq",

        "shared_workflow":
            "RevTrace Core",
    }


# =======================================================
# PROSPECT ROUTES
# =======================================================

@app.get("/prospects")
def list_prospects():

    return {
        "prospects":
            get_all_prospects()
    }


@app.get(
    "/prospects/{prospect_id}"
)
def get_single_prospect(
    prospect_id: str
):

    return get_prospect_or_404(
        prospect_id
    )


@app.post("/prospects")
def create_prospect(
    data: ProspectCreate
):

    prospect_id = str(
        uuid.uuid4()
    )[:8]

    # ---------------------------------------------------
    # CREATE SHARED REVTRACE ACCOUNT FIRST
    # ---------------------------------------------------

    try:

        core_account = create_core_account(
            company=data.company,
            contact_name=data.name,
            industry=data.industry,
            role=data.role,
        )

        account_id = core_account[
            "account_id"
        ]

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not create shared "
                "RevTrace account. "
                "Make sure RevTrace Core "
                "is running on port 8100. "
                f"Error: {exc}"
            ),
        )

    # ---------------------------------------------------
    # CREATE LOCAL PROSPECT
    # ---------------------------------------------------

    prospect = {

        "prospect_id":
            prospect_id,

        "account_id":
            account_id,

        "name":
            data.name,

        "company":
            data.company,

        "industry":
            data.industry,

        "role":
            data.role,

        "company_size":
            data.company_size,

        "pain_point":
            data.pain_point,

        "message_angle":
            None,

        "message_sent":
            None,

        "outcome":
            None,

        "stage":
            "NEW_PROSPECT",
    }

    insert_prospect(
        prospect
    )

    # ---------------------------------------------------
    # SHARED JOURNEY EVENT
    # ---------------------------------------------------

    safe_core_event(

        prospect=prospect,

        event_type=
            "PROSPECT_CREATED",

        stage=
            "NEW_PROSPECT",

        summary=(
            f"{data.company} prospect "
            f"{data.name} created for "
            f"outbound prospecting."
        ),

        payload={
            "prospect_id":
                prospect_id,

            "contact_name":
                data.name,

            "industry":
                data.industry,

            "role":
                data.role,

            "company_size":
                data.company_size,

            "pain_point":
                data.pain_point,
        },
    )

    return prospect


# =======================================================
# HINDSIGHT ANALYSIS
# =======================================================

@app.post(
    "/prospects/{prospect_id}/analyze"
)
def analyze_prospect(
    prospect_id: str
):

    prospect = get_prospect_or_404(
        prospect_id
    )

    # ---------------------------------------------------
    # HINDSIGHT RECALL
    # ---------------------------------------------------

    memories = (
        recall_similar_prospects(
            industry=
                prospect["industry"],

            role=
                prospect["role"],

            company_size=
                prospect[
                    "company_size"
                ],

            pain_point=
                prospect[
                    "pain_point"
                ],
        )
    )

    # ---------------------------------------------------
    # FIND COMPARABLE PROSPECTS
    # ---------------------------------------------------

    comparable = (
        filter_comparable_prospects(
            memories,

            industry=
                prospect["industry"],

            role=
                prospect["role"],

            company_size=
                prospect[
                    "company_size"
                ],
        )
    )

    # ---------------------------------------------------
    # ANALYZE HISTORICAL OUTCOMES
    # ---------------------------------------------------

    analysis = analyze_prospects(
        comparable
    )

    recommended_angle = (
        analysis[
            "recommended_angle"
        ]
    )

    if not recommended_angle:
        recommended_angle = (
            "Problem-Solution"
        )

    update_analysis(
        prospect_id,
        recommended_angle,
    )

    prospect[
        "message_angle"
    ] = recommended_angle

    # ---------------------------------------------------
    # SHARED JOURNEY MEMORY
    # ---------------------------------------------------

    safe_core_event(

        prospect=prospect,

        event_type=
            "PROSPECT_ANALYZED",

        stage=
            prospect.get(
                "stage",
                "NEW_PROSPECT",
            ),

        summary=(
            f"Hindsight analyzed "
            f"{prospect['company']} and "
            f"recommended the "
            f"{recommended_angle} "
            f"messaging angle."
        ),

        payload={
            "recommended_angle":
                recommended_angle,

            "confidence":
                analysis.get(
                    "confidence"
                ),

            "evidence_count":
                analysis.get(
                    "evidence_count"
                ),

            "comparable_prospects":
                len(comparable),

            "raw_memories_recalled":
                len(memories),
        },
    )

    return {

        "prospect":
            prospect,

        "memory": {

            "provider":
                "Hindsight Cloud",

            "operation":
                "RECALL",

            "raw_memories_recalled":
                len(memories),

            "comparable_prospects":
                len(comparable),

            "status":
                "RECALL_COMPLETED",
        },

        "analysis":
            analysis,

        "comparable_prospects":
            comparable,

        "shared_account": {
            "account_id":
                prospect.get(
                    "account_id"
                ),

            "provider":
                "RevTrace Core",
        },
    }


# =======================================================
# MESSAGE GENERATION
# =======================================================

@app.post(
    "/prospects/{prospect_id}/generate-message"
)
def generate_message(
    prospect_id: str
):

    prospect = get_prospect_or_404(
        prospect_id
    )

    memories = (
        recall_similar_prospects(
            industry=
                prospect["industry"],

            role=
                prospect["role"],

            company_size=
                prospect[
                    "company_size"
                ],

            pain_point=
                prospect[
                    "pain_point"
                ],
        )
    )

    comparable = (
        filter_comparable_prospects(
            memories,

            industry=
                prospect["industry"],

            role=
                prospect["role"],

            company_size=
                prospect[
                    "company_size"
                ],
        )
    )

    analysis = analyze_prospects(
        comparable
    )

    recommended_angle = (
        analysis[
            "recommended_angle"
        ]
    )

    if not recommended_angle:
        recommended_angle = (
            "Problem-Solution"
        )

    message = (
        generate_outreach_message(
            name=
                prospect["name"],

            company=
                prospect["company"],

            industry=
                prospect["industry"],

            role=
                prospect["role"],

            company_size=
                prospect[
                    "company_size"
                ],

            pain_point=
                prospect[
                    "pain_point"
                ],

            recommended_angle=
                recommended_angle,

            memories=
                comparable,
        )
    )

    update_message(
        prospect_id,
        recommended_angle,
        message,
    )

    prospect[
        "stage"
    ] = "OUTREACH_SENT"

    prospect[
        "message_angle"
    ] = recommended_angle

    prospect[
        "message_sent"
    ] = message

    # ---------------------------------------------------
    # SHARED JOURNEY EVENT
    # ---------------------------------------------------

    safe_core_event(

        prospect=prospect,

        event_type=
            "OUTREACH_GENERATED",

        stage=
            "OUTREACH_SENT",

        summary=(
            f"Outbound message generated "
            f"for {prospect['company']} "
            f"using the "
            f"{recommended_angle} strategy."
        ),

        payload={
            "prospect_id":
                prospect_id,

            "message_angle":
                recommended_angle,

            "confidence":
                analysis.get(
                    "confidence"
                ),

            "evidence_count":
                analysis.get(
                    "evidence_count"
                ),

            "message":
                message,
        },
    )

    return {

        "prospect_id":
            prospect_id,

        "account_id":
            prospect.get(
                "account_id"
            ),

        "stage":
            "OUTREACH_SENT",

        "memory": {

            "provider":
                "Hindsight Cloud",

            "operation":
                "RECALL",

            "raw_memories_recalled":
                len(memories),

            "comparable_prospects":
                len(comparable),

            "status":
                "RECALL_COMPLETED",
        },

        "recommended_angle":
            recommended_angle,

        "confidence":
            analysis[
                "confidence"
            ],

        "evidence_count":
            analysis[
                "evidence_count"
            ],

        "success_rate":
            analysis[
                "success_rate"
            ],

        "message":
            message,
    }


# =======================================================
# OUTCOME + LEARNING
# =======================================================

@app.post(
    "/prospects/{prospect_id}/outcome"
)
def save_outcome(
    prospect_id: str,
    data: OutcomeUpdate,
):

    prospect = get_prospect_or_404(
        prospect_id
    )

    allowed_outcomes = {
        "NO_RESPONSE",
        "REPLIED",
        "MEETING_BOOKED",
        "QUALIFIED",
        "CONVERTED_TO_DEAL",
    }

    if (
        data.outcome
        not in allowed_outcomes
    ):
        raise HTTPException(
            status_code=400,

            detail=(
                "Invalid outcome. "
                f"Allowed outcomes: "
                f"{sorted(allowed_outcomes)}"
            ),
        )

    # ---------------------------------------------------
    # DETERMINE NEXT SALES STAGE
    # ---------------------------------------------------

    if data.outcome == "REPLIED":

        next_stage = (
            "ENGAGED_PROSPECT"
        )

    elif (
        data.outcome
        == "MEETING_BOOKED"
    ):

        next_stage = (
            "MEETING_SCHEDULED"
        )

    elif data.outcome in {
        "QUALIFIED",
        "CONVERTED_TO_DEAL",
    }:

        next_stage = (
            "QUALIFIED_OPPORTUNITY"
        )

    elif (
        data.outcome
        == "NO_RESPONSE"
    ):

        next_stage = (
            "OUTREACH_SENT"
        )

    else:

        next_stage = (
            "OUTREACH_SENT"
        )

    # ---------------------------------------------------
    # SAVE LOCALLY
    # ---------------------------------------------------

    update_outcome(
        prospect_id,
        data.outcome,
        next_stage,
    )

    prospect[
        "outcome"
    ] = data.outcome

    prospect[
        "stage"
    ] = next_stage

    # ---------------------------------------------------
    # SPECIALIZED PROSPECTING HINDSIGHT MEMORY
    # ---------------------------------------------------

    retain_prospect_memory(
        prospect_id=
            prospect[
                "prospect_id"
            ],

        industry=
            prospect[
                "industry"
            ],

        role=
            prospect[
                "role"
            ],

        company_size=
            prospect[
                "company_size"
            ],

        pain_point=
            prospect[
                "pain_point"
            ],

        message_angle=(
            prospect[
                "message_angle"
            ]
            or "Unknown"
        ),

        outcome=
            data.outcome,
    )

    # ---------------------------------------------------
    # SHARED REVTRACE JOURNEY MEMORY
    # ---------------------------------------------------

    safe_core_event(

        prospect=prospect,

        event_type=
            "OUTREACH_OUTCOME",

        stage=
            next_stage,

        summary=(
            f"{prospect['company']} "
            f"outreach outcome was "
            f"{data.outcome}."
        ),

        payload={
            "prospect_id":
                prospect_id,

            "outcome":
                data.outcome,

            "message_angle":
                prospect.get(
                    "message_angle"
                ),

            "pain_point":
                prospect.get(
                    "pain_point"
                ),
        },
    )

    return {

        "message":
            "Outcome saved locally, "
            "retained in Prospecting memory, "
            "and synchronized with RevTrace Core",

        "account_id":
            prospect.get(
                "account_id"
            ),

        "stage":
            next_stage,

        "memory": {

            "provider":
                "Hindsight Cloud",

            "operation":
                "RETAIN",

            "status":
                "MEMORY_STORED",

            "prospect_id":
                prospect_id,

            "outcome":
                data.outcome,
        },

        "shared_memory": {

            "provider":
                "RevTrace Core + "
                "Hindsight Cloud",

            "status":
                "JOURNEY_SYNCED",
        },

        "prospect":
            prospect,
    }


# =======================================================
# MEETING SCHEDULING
# =======================================================

@app.post(
    "/prospects/{prospect_id}/schedule-meeting"
)
def create_meeting(
    prospect_id: str,
    data: MeetingCreate,
):

    prospect = get_prospect_or_404(
        prospect_id
    )

    if prospect.get(
        "stage"
    ) not in {
        "ENGAGED_PROSPECT",
        "MEETING_SCHEDULED",
        "OUTREACH_SENT",
    }:

        raise HTTPException(
            status_code=400,

            detail=(
                "Prospect is not currently "
                "ready for meeting scheduling."
            ),
        )

    schedule_meeting(
        prospect_id,
        data.meeting_date,
        data.meeting_time,
    )

    prospect[
        "stage"
    ] = "MEETING_SCHEDULED"

    prospect[
        "meeting_status"
    ] = "SCHEDULED"

    prospect[
        "meeting_date"
    ] = data.meeting_date

    prospect[
        "meeting_time"
    ] = data.meeting_time

    # ---------------------------------------------------
    # SHARED JOURNEY EVENT
    # ---------------------------------------------------

    safe_core_event(

        prospect=prospect,

        event_type=
            "MEETING_SCHEDULED",

        stage=
            "MEETING_SCHEDULED",

        summary=(
            f"Discovery meeting with "
            f"{prospect['company']} "
            f"scheduled for "
            f"{data.meeting_date} "
            f"at {data.meeting_time}."
        ),

        payload={
            "prospect_id":
                prospect_id,

            "meeting_date":
                data.meeting_date,

            "meeting_time":
                data.meeting_time,

            "meeting_status":
                "SCHEDULED",
        },
    )

    return {

        "message":
            "Meeting scheduled",

        "account_id":
            prospect.get(
                "account_id"
            ),

        "prospect_id":
            prospect_id,

        "company":
            prospect["company"],

        "meeting_date":
            data.meeting_date,

        "meeting_time":
            data.meeting_time,

        "meeting_status":
            "SCHEDULED",

        "stage":
            "MEETING_SCHEDULED",

        "next_action":
            "ATTEND_MEETING",
    }


# =======================================================
# MEETING COMPLETION + DEAL DESK HANDOFF
# =======================================================

@app.post(
    "/prospects/{prospect_id}/complete-meeting"
)
def mark_meeting_complete(
    prospect_id: str
):

    prospect = get_prospect_or_404(
        prospect_id
    )

    if (
        prospect.get(
            "meeting_status"
        )
        != "SCHEDULED"
    ):

        raise HTTPException(
            status_code=400,

            detail=(
                "No scheduled meeting "
                "exists for this prospect."
            ),
        )

    complete_meeting(
        prospect_id
    )

    # ---------------------------------------------------
    # CREATE SHARED OPPORTUNITY
    # ---------------------------------------------------

    opportunity_id = (
        "OPP-"
        + uuid.uuid4().hex[:6].upper()
    )

    prospect[
        "stage"
    ] = "QUALIFIED_OPPORTUNITY"

    prospect[
        "meeting_status"
    ] = "COMPLETED"

    # ---------------------------------------------------
    # RECORD PROSPECTING COMPLETION IN SHARED MEMORY
    # ---------------------------------------------------

    safe_core_event(

        prospect=prospect,

        opportunity_id=
            opportunity_id,

        event_type=
            "MEETING_COMPLETED",

        stage=
            "QUALIFIED_OPPORTUNITY",

        summary=(
            f"Discovery meeting with "
            f"{prospect['company']} "
            f"was completed and the "
            f"prospect became a qualified "
            f"opportunity."
        ),

        payload={
            "prospect_id":
                prospect_id,

            "meeting_status":
                "COMPLETED",

            "message_angle":
                prospect.get(
                    "message_angle"
                ),

            "outreach_outcome":
                prospect.get(
                    "outcome"
                ),

            "pain_point":
                prospect.get(
                    "pain_point"
                ),
        },
    )

    # ---------------------------------------------------
    # HAND OFF OWNERSHIP TO DEAL DESK
    # ---------------------------------------------------

    core_handoff_status = (
        "HANDOFF_PENDING"
    )

    try:

        update_core_stage(

            account_id=
                prospect[
                    "account_id"
                ],

            stage=
                "QUALIFIED_OPPORTUNITY",

            current_agent=
                "DEAL_DESK",

            opportunity_id=
                opportunity_id,
        )

        core_handoff_status = (
            "HANDOFF_READY"
        )

    except Exception as exc:

        print(
            "Deal Desk handoff warning:",
            exc,
        )

    return {

        "message":
            "Meeting completed",

        "account_id":
            prospect.get(
                "account_id"
            ),

        "opportunity_id":
            opportunity_id,

        "prospect_id":
            prospect_id,

        "company":
            prospect["company"],

        "meeting_status":
            "COMPLETED",

        "stage":
            "QUALIFIED_OPPORTUNITY",

        "current_agent":
            "DEAL_DESK",

        "handoff_status":
            core_handoff_status,

        "next_step":
            "HANDOFF_TO_DEAL_DESK",
    }


# =======================================================
# SHUTDOWN
# =======================================================

@app.on_event("shutdown")
def shutdown_event():

    try:
        hindsight_client.close()

    except Exception:
        pass