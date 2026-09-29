import streamlit as st

from core.document_loader import load_document
from core.hindsight_memory import HindsightMemory
from core.rfp_analyzer import analyze_rfp
from core.proposal_generator import generate_proposal
from core.reviewer import review_proposal

from core.revtrace_core import (
    get_accounts,
    get_account,
    get_latest_commercial_decision,
    send_core_event,
    update_core_stage,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="RevTrace Proposal / RFP Agent",
    layout="wide",
)


# ============================================================
# DARK THEME
# ============================================================

st.markdown(
    """
<style>
.stApp {
    background: #090d17;
    color: #f8fafc;
}

[data-testid="stHeader"] {
    background: rgba(9, 13, 23, 0.96);
}

[data-testid="stSidebar"] {
    background: #0c1220;
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3, h4 {
    color: #f8fafc !important;
}

p, label {
    color: #cbd5e1;
}

div[data-testid="stMetric"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 14px;
}

div[data-testid="stMetricLabel"] {
    color: #94a3b8;
}

div[data-testid="stMetricValue"] {
    color: #f8fafc;
    font-size: 1rem;
}

div[data-baseweb="select"] > div {
    background: #111827;
    color: #f8fafc;
    border-color: rgba(139,92,246,0.45);
}

input, textarea {
    background: #111827 !important;
    color: #f8fafc !important;
}

[data-testid="stFileUploader"] {
    background: #111827;
    border-radius: 12px;
}

[data-testid="stExpander"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}

[data-baseweb="tab-list"] {
    gap: 8px;
}

[data-baseweb="tab"] {
    background: #111827;
    border-radius: 10px 10px 0 0;
    padding-left: 20px;
    padding-right: 20px;
}

hr {
    border-color: rgba(255,255,255,0.08);
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def stage_label(value):
    if not value:
        return "Unknown"

    return (
        str(value)
        .replace("_", " ")
        .title()
    )


def clear_account_specific_work():
    """
    Prevent one customer's RFP/proposal data
    from appearing under another account.
    """

    keys = [
        "rfp_text",
        "rfp_filename",
        "requirements",
        "evidence",
        "proposal",
        "review",
        "proposal_submitted",
        "final_outcome",
    ]

    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def initialize_state():
    defaults = {
        "rfp_text": None,
        "rfp_filename": None,
        "requirements": None,
        "evidence": None,
        "proposal": None,
        "review": None,
        "historical_lessons": "",
        "proposal_submitted": False,
        "final_outcome": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# LOAD ACCOUNTS
# ============================================================

try:
    accounts = get_accounts()

    accounts = sorted(
        accounts,
        key=lambda item: item.get(
            "updated_at",
            item.get("created_at", "")
        ),
        reverse=True,
    )

except Exception as exc:
    st.error(
        "RevTrace Core is not reachable."
    )

    st.code(str(exc))
    st.stop()


if not accounts:
    st.info(
        "No RevTrace accounts exist yet. "
        "Create a prospect in the Prospecting Agent."
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1]
)


with header_left:
    st.caption(
        "🟠 REVTRACE • PROPOSAL INTELLIGENCE"
    )

    st.title(
        "Proposal / RFP Agent"
    )

    st.caption(
        "Evidence-grounded proposals powered by "
        "Hindsight memory and Deal Desk approvals."
    )


with header_right:
    st.write("")

    if st.button(
        "↻ Refresh",
        use_container_width=True,
    ):
        st.rerun()


st.divider()


# ============================================================
# ACCOUNT WORKSPACE
# ============================================================

st.caption(
    "REVTRACE ACCOUNT WORKSPACE"
)

st.subheader(
    "Select Customer Account"
)

st.caption(
    "Every RevTrace account is visible here. "
    "Proposal actions unlock only after "
    "Deal Desk commercial approval."
)


account_map = {
    account["account_id"]: account
    for account in accounts
}


account_ids = list(
    account_map.keys()
)


saved_account_id = (
    st.session_state.get(
        "selected_rfp_account"
    )
)


if saved_account_id not in account_ids:
    saved_account_id = account_ids[0]


selected_index = account_ids.index(
    saved_account_id
)


selected_account_id = st.selectbox(
    "RevTrace Account",

    options=account_ids,

    index=selected_index,

    format_func=lambda account_id:
        (
            f"{account_map[account_id].get('company', 'Unknown')} "
            f"— "
            f"{stage_label(account_map[account_id].get('stage'))}"
        ),
)


# ============================================================
# ACCOUNT SWITCH PROTECTION
# ============================================================

previous_active_account = (
    st.session_state.get(
        "active_rfp_account"
    )
)


if (
    previous_active_account
    != selected_account_id
):
    clear_account_specific_work()

    st.session_state[
        "active_rfp_account"
    ] = selected_account_id


st.session_state[
    "selected_rfp_account"
] = selected_account_id


initialize_state()


# ============================================================
# SELECTED ACCOUNT
# ============================================================

try:
    core_data = get_account(
        selected_account_id
    )

    account = core_data.get(
        "account",
        {}
    )

    journey_events = core_data.get(
        "events",
        []
    )

    commercial_decision = (
        get_latest_commercial_decision(
            selected_account_id
        )
    )

except Exception as exc:
    st.error(
        f"Could not load selected account: {exc}"
    )

    st.stop()


ACCOUNT_ID = account.get(
    "account_id"
)

OPPORTUNITY_ID = account.get(
    "opportunity_id"
)

CURRENT_STAGE = account.get(
    "stage"
)

CURRENT_AGENT = account.get(
    "current_agent"
)


# ============================================================
# STAGE GATING
# ============================================================

proposal_ready = (
    CURRENT_AGENT == "PROPOSAL_RFP"
    or
    CURRENT_STAGE in {
        "COMMERCIAL_APPROVED",
        "PROPOSAL_DRAFT",
    }
)


proposal_already_submitted = (
    CURRENT_STAGE in {
        "PROPOSAL_SUBMITTED",
        "WON",
        "LOST",
    }
)


completed_journey = (
    CURRENT_STAGE in {
        "WON",
        "LOST",
    }
)


# ============================================================
# ACCOUNT SUMMARY
# ============================================================

st.subheader(
    "Selected Account"
)


c1, c2, c3, c4, c5 = st.columns(5)


with c1:
    st.metric(
        "Company",
        account.get(
            "company",
            "Unknown",
        ),
    )


with c2:
    st.metric(
        "Account ID",
        ACCOUNT_ID or "—",
    )


with c3:
    st.metric(
        "Opportunity",
        OPPORTUNITY_ID
        or
        "Not created",
    )


with c4:
    st.metric(
        "Stage",
        stage_label(
            CURRENT_STAGE
        ),
    )


with c5:
    st.metric(
        "Current Agent",
        stage_label(
            CURRENT_AGENT
        ),
    )


# ============================================================
# JOURNEY
# ============================================================

st.subheader(
    "Revenue Journey"
)


flow1, flow2, flow3, flow4, flow5 = (
    st.columns(5)
)


with flow1:
    st.success(
        "✓ Prospecting"
    )


with flow2:
    if OPPORTUNITY_ID:
        st.success(
            "✓ Meeting"
        )
    else:
        st.info(
            "○ Meeting"
        )


with flow3:
    if commercial_decision:
        st.success(
            "✓ Deal Desk"
        )

    elif CURRENT_STAGE in {
        "QUALIFIED_OPPORTUNITY",
        "DEAL_DESK",
    }:
        st.info(
            "● Deal Desk"
        )

    else:
        st.info(
            "○ Deal Desk"
        )


with flow4:
    if proposal_already_submitted:
        st.success(
            "✓ Proposal / RFP"
        )

    elif proposal_ready:
        st.info(
            "● Proposal / RFP"
        )

    else:
        st.info(
            "○ Proposal / RFP"
        )


with flow5:
    if CURRENT_STAGE == "WON":
        st.success(
            "✓ WON"
        )

    elif CURRENT_STAGE == "LOST":
        st.error(
            "✓ LOST"
        )

    else:
        st.info(
            "○ Won / Lost"
        )


# ============================================================
# DEAL DESK CONTEXT
# ============================================================

if commercial_decision:

    st.subheader(
        "Deal Desk Commercial Context"
    )


    d1, d2, d3, d4 = (
        st.columns(4)
    )


    with d1:
        st.caption(
            "Requested Terms"
        )

        st.write(
            commercial_decision.get(
                "requested_terms"
            )
            or
            "Not available"
        )


    with d2:
        st.caption(
            "Approved Final Terms"
        )

        st.success(
            commercial_decision.get(
                "final_terms"
            )
            or
            "Not available"
        )


    with d3:
        st.caption(
            "Decision"
        )

        st.write(
            stage_label(
                commercial_decision.get(
                    "decision"
                )
            )
        )


    with d4:
        st.caption(
            "Approved By"
        )

        st.write(
            commercial_decision.get(
                "approver"
            )
            or
            "Unknown"
        )


# ============================================================
# CURRENT STATUS
# ============================================================

if proposal_ready:

    st.success(
        "✓ Proposal workspace unlocked. "
        "Deal Desk has approved commercial terms "
        "for this opportunity."
    )


elif proposal_already_submitted:

    if CURRENT_STAGE == "WON":
        st.success(
            "✓ This account has completed the "
            "revenue journey and is WON."
        )

    elif CURRENT_STAGE == "LOST":
        st.error(
            "This account has completed the "
            "revenue journey and is LOST."
        )

    else:
        st.info(
            f"This account is already at "
            f"{stage_label(CURRENT_STAGE)}. "
            f"Its existing proposal journey "
            f"can be inspected below."
        )


else:

    st.warning(
        f"🔒 Proposal workspace locked. "
        f"{account.get('company', 'This account')} "
        f"is currently at "
        f"{stage_label(CURRENT_STAGE)}. "
        f"Proposal generation unlocks after "
        f"Deal Desk commercial approval."
    )


# ============================================================
# JOURNEY HISTORY
# ============================================================

with st.expander(
    "View Complete RevTrace Journey History"
):

    if not journey_events:
        st.write(
            "No account events yet."
        )

    else:
        for event in reversed(
            journey_events
        ):

            st.markdown(
                f"""
**{stage_label(event.get('event_type'))}**

Agent: `{stage_label(event.get('agent'))}`  
Stage: `{stage_label(event.get('stage'))}`

{event.get('summary', '')}

---
"""
            )


# ============================================================
# HINDSIGHT
# ============================================================

memory = HindsightMemory()


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "Organizational Memory",
        "RFP Analysis",
        "Proposal & Review",
    ]
)


# ============================================================
# TAB 1 — ORGANIZATIONAL MEMORY
# ============================================================

with tab1:

    st.header(
        "Build Organizational Memory"
    )

    st.caption(
        "Historical proposals, policies, "
        "case studies and capability documents "
        "become reusable organizational memory."
    )


    uploaded_files = st.file_uploader(
        "Upload organizational documents",

        type=[
            "pdf",
            "docx",
            "txt",
            "md",
        ],

        accept_multiple_files=True,

        key="organizational_files",
    )


    document_type = st.selectbox(
        "Document Type",

        [
            "historical_proposal",
            "case_study",
            "policy",
            "capability",
        ],
    )


    historical_outcome = st.selectbox(
        "Historical Outcome",

        [
            "Won",
            "Lost",
            "Unknown",
        ],
    )


    historical_customer = st.text_input(
        "Customer / Industry"
    )


    if st.button(
        "Store in Hindsight",
        type="primary",
    ):

        if not uploaded_files:
            st.warning(
                "Upload at least one document."
            )

        else:
            for file in uploaded_files:

                try:
                    content = load_document(
                        file.name,
                        file.getvalue(),
                    )


                    if not content.strip():
                        st.warning(
                            f"{file.name} contains no readable text."
                        )

                        continue


                    memory.retain_document(
                        content=content,
                        filename=file.name,
                        document_type=document_type,
                        outcome=historical_outcome,
                        customer=historical_customer,
                    )


                    st.success(
                        f"Stored in Hindsight: {file.name}"
                    )


                except Exception as exc:
                    st.error(
                        f"{file.name}: {exc}"
                    )


    st.divider()


    if st.button(
        "Reflect on Historical Experience"
    ):

        try:
            with st.spinner(
                "Reflecting on organizational memory..."
            ):

                lessons = memory.reflect(
                    """
Analyze historical proposals,
case studies, policies and
organizational knowledge.

Identify:

1. recurring reasons for winning
2. recurring reasons for losing
3. evidence gaps
4. unsupported claims to avoid
5. important organizational capabilities
6. recurring customer requirements

Clearly distinguish documented facts
from inference.
"""
                )


            st.session_state[
                "historical_lessons"
            ] = lessons


        except Exception as exc:
            st.error(
                f"Historical reflection failed: {exc}"
            )


    if st.session_state[
        "historical_lessons"
    ]:

        st.markdown(
            st.session_state[
                "historical_lessons"
            ]
        )


# ============================================================
# TAB 2 — RFP ANALYSIS
# ============================================================

with tab2:

    st.header(
        "Analyze Customer RFP"
    )


    st.caption(
        f"Selected account: "
        f"{account.get('company')} · "
        f"{ACCOUNT_ID}"
    )


    analysis_enabled = (
        proposal_ready
    )


    if not analysis_enabled:

        st.warning(
            "RFP analysis is locked for "
            "this account. Deal Desk commercial "
            "approval is required first."
        )


    rfp_file = st.file_uploader(
        "Upload RFP",

        type=[
            "pdf",
            "docx",
            "txt",
            "md",
        ],

        key=
            f"rfp_upload_{ACCOUNT_ID}",

        disabled=
            not analysis_enabled,
    )


    if (
        analysis_enabled
        and
        rfp_file
    ):

        try:
            rfp_text = load_document(
                rfp_file.name,
                rfp_file.getvalue(),
            )


            st.session_state[
                "rfp_text"
            ] = rfp_text


            st.session_state[
                "rfp_filename"
            ] = rfp_file.name


            st.info(
                f"Extracted "
                f"{len(rfp_text):,} "
                f"characters."
            )


            with st.expander(
                "Preview extracted RFP"
            ):
                st.text(
                    rfp_text[:10000]
                )


        except Exception as exc:
            st.error(
                f"RFP extraction failed: {exc}"
            )


    extract_disabled = (
        not analysis_enabled
        or
        not st.session_state[
            "rfp_text"
        ]
    )


    if st.button(
        "Extract Requirements",
        type="primary",
        disabled=extract_disabled,
    ):

        try:
            with st.spinner(
                "Extracting RFP requirements..."
            ):

                requirements = analyze_rfp(
                    st.session_state[
                        "rfp_text"
                    ]
                )


            st.session_state[
                "requirements"
            ] = requirements


            send_core_event(
                account_id=ACCOUNT_ID,
                opportunity_id=OPPORTUNITY_ID,
                event_type="RFP_ANALYZED",
                stage="PROPOSAL_DRAFT",

                summary=(
                    f"RFP for "
                    f"{account.get('company')} "
                    f"was analyzed and "
                    f"{len(requirements)} "
                    f"requirements were extracted."
                ),

                payload={
                    "requirements_count":
                        len(requirements),

                    "rfp_filename":
                        st.session_state[
                            "rfp_filename"
                        ],
                },
            )


            update_core_stage(
                account_id=ACCOUNT_ID,
                stage="PROPOSAL_DRAFT",
                current_agent="PROPOSAL_RFP",
                opportunity_id=OPPORTUNITY_ID,
            )


            st.success(
                f"Extracted "
                f"{len(requirements)} "
                f"requirements."
            )


        except Exception as exc:
            st.error(
                f"Requirement extraction failed: {exc}"
            )


    if st.session_state[
        "requirements"
    ]:

        st.subheader(
            "Extracted Requirements"
        )


        st.dataframe(
            st.session_state[
                "requirements"
            ],
            use_container_width=True,
        )


# ============================================================
# TAB 3 — PROPOSAL
# ============================================================

with tab3:

    st.header(
        "Generate and Review Proposal"
    )


    if commercial_decision:

        st.success(
            "Deal Desk approved terms: "
            f"{commercial_decision.get('final_terms')}"
        )


    if not proposal_ready:

        if proposal_already_submitted:

            st.info(
                "Proposal workflow has already "
                f"progressed to "
                f"{stage_label(CURRENT_STAGE)}."
            )

        else:
            st.warning(
                "Proposal generation is locked "
                "until commercial approval."
            )


    can_generate = (
        proposal_ready
        and
        bool(
            st.session_state[
                "rfp_text"
            ]
        )
        and
        bool(
            st.session_state[
                "requirements"
            ]
        )
        and
        bool(
            commercial_decision
        )
    )


    if st.button(
        "Retrieve Memory + Generate Proposal",
        type="primary",
        disabled=not can_generate,
    ):

        requirements = (
            st.session_state[
                "requirements"
            ]
        )


        evidence = []


        # ----------------------------------------------------
        # HINDSIGHT RECALL
        # ----------------------------------------------------

        try:
            with st.spinner(
                "Retrieving organizational memory..."
            ):

                for requirement in requirements:

                    query = f"""
RFP requirement:

{requirement['requirement']}

Find relevant organizational:
- capabilities
- historical proposals
- case studies
- policies
- evidence
- limitations
- historical lessons

Do not invent facts.
"""


                    memories = memory.recall(
                        query
                    )


                    evidence.append(
                        {
                            "requirement":
                                requirement[
                                    "requirement"
                                ],

                            "requirement_id":
                                requirement[
                                    "id"
                                ],

                            "memories":
                                memories,
                        }
                    )


            st.session_state[
                "evidence"
            ] = evidence


            st.success(
                "Organizational memory retrieved."
            )


        except Exception as exc:
            st.error(
                f"Hindsight recall failed: {exc}"
            )

            evidence = []


        # ----------------------------------------------------
        # GENERATION
        # ----------------------------------------------------

        if evidence:

            try:
                account_context = {
                    "account_id":
                        ACCOUNT_ID,

                    "opportunity_id":
                        OPPORTUNITY_ID,

                    "company":
                        account.get(
                            "company"
                        ),

                    "industry":
                        account.get(
                            "industry"
                        ),

                    "contact_name":
                        account.get(
                            "contact_name"
                        ),

                    "role":
                        account.get(
                            "role"
                        ),
                }


                with st.spinner(
                    "Generating evidence-grounded proposal..."
                ):

                    proposal = generate_proposal(
                        st.session_state[
                            "rfp_text"
                        ],

                        requirements,

                        evidence,

                        st.session_state[
                            "historical_lessons"
                        ],

                        commercial_context=
                            commercial_decision,

                        account_context=
                            account_context,
                    )


                st.session_state[
                    "proposal"
                ] = proposal


                send_core_event(
                    account_id=ACCOUNT_ID,
                    opportunity_id=OPPORTUNITY_ID,
                    event_type="PROPOSAL_GENERATED",
                    stage="PROPOSAL_DRAFT",

                    summary=(
                        f"Proposal draft generated "
                        f"for "
                        f"{account.get('company')} "
                        f"using Hindsight evidence "
                        f"and approved commercial terms."
                    ),

                    payload={
                        "approved_terms":
                            commercial_decision.get(
                                "final_terms"
                            ),

                        "requirements_count":
                            len(requirements),
                    },
                )


                update_core_stage(
                    account_id=ACCOUNT_ID,
                    stage="PROPOSAL_DRAFT",
                    current_agent="PROPOSAL_RFP",
                    opportunity_id=OPPORTUNITY_ID,
                )


                st.success(
                    "Proposal generated."
                )


            except Exception as exc:
                st.error(
                    f"Proposal generation failed: {exc}"
                )


        # ----------------------------------------------------
        # REVIEW
        # ----------------------------------------------------

        if st.session_state[
            "proposal"
        ]:

            try:
                with st.spinner(
                    "Running independent factual review..."
                ):

                    review = review_proposal(
                        st.session_state[
                            "rfp_text"
                        ],

                        requirements,

                        st.session_state[
                            "proposal"
                        ],

                        evidence,
                    )


                st.session_state[
                    "review"
                ] = review


                st.success(
                    "Proposal independently reviewed."
                )


            except Exception as exc:
                st.warning(
                    f"Reviewer issue: {exc}"
                )


# ============================================================
# GENERATED PROPOSAL
# ============================================================

if st.session_state[
    "proposal"
]:

    st.divider()


    st.subheader(
        f"Generated Proposal — "
        f"{account.get('company')}"
    )


    st.markdown(
        st.session_state[
            "proposal"
        ]
    )


    if (
        not st.session_state[
            "proposal_submitted"
        ]
        and
        CURRENT_STAGE not in {
            "PROPOSAL_SUBMITTED",
            "WON",
            "LOST",
        }
    ):

        if st.button(
            "Submit Proposal",
            type="primary",
        ):

            try:
                send_core_event(
                    account_id=ACCOUNT_ID,
                    opportunity_id=OPPORTUNITY_ID,
                    event_type="PROPOSAL_SUBMITTED",
                    stage="PROPOSAL_SUBMITTED",

                    summary=(
                        f"Proposal submitted to "
                        f"{account.get('company')}."
                    ),

                    payload={
                        "commercial_terms":
                            (
                                commercial_decision.get(
                                    "final_terms"
                                )
                                if commercial_decision
                                else None
                            ),
                    },
                )


                update_core_stage(
                    account_id=ACCOUNT_ID,
                    stage="PROPOSAL_SUBMITTED",
                    current_agent="PROPOSAL_RFP",
                    opportunity_id=OPPORTUNITY_ID,
                )


                st.session_state[
                    "proposal_submitted"
                ] = True


                st.success(
                    "Proposal submitted and "
                    "RevTrace journey updated."
                )


            except Exception as exc:
                st.error(
                    f"Proposal submission failed: {exc}"
                )


# ============================================================
# REVIEW RESULTS
# ============================================================

if st.session_state[
    "review"
]:

    review = (
        st.session_state[
            "review"
        ]
    )


    st.divider()


    st.subheader(
        "Independent Proposal Review"
    )


    coverage = review.get(
        "coverage",
        []
    )


    if coverage:
        st.markdown(
            "#### Requirement Coverage"
        )

        st.dataframe(
            coverage,
            use_container_width=True,
        )


    gaps = review.get(
        "gaps",
        []
    )


    if gaps:
        st.markdown(
            "#### Evidence Gaps"
        )

        for gap in gaps:
            st.warning(
                gap
            )


    unsupported = review.get(
        "unsupported_claims",
        []
    )


    if unsupported:
        st.markdown(
            "#### Unsupported Claims"
        )

        for item in unsupported:
            st.error(
                item
            )


    human_verification = review.get(
        "human_verification",
        []
    )


    if human_verification:
        st.markdown(
            "#### Human Verification"
        )

        for item in human_verification:
            st.info(
                item
            )


# ============================================================
# HISTORICAL PROPOSAL STATUS
# ============================================================

if CURRENT_STAGE in {
    "PROPOSAL_SUBMITTED",
    "WON",
    "LOST",
}:

    st.divider()

    st.subheader(
        "Proposal Status"
    )


    if (
        CURRENT_STAGE
        == "PROPOSAL_SUBMITTED"
    ):

        st.info(
            "Proposal has been submitted. "
            "Waiting for final customer outcome."
        )


    elif (
        CURRENT_STAGE
        == "WON"
    ):

        st.success(
            "✓ Opportunity WON"
        )


    elif (
        CURRENT_STAGE
        == "LOST"
    ):

        st.error(
            "Opportunity LOST"
        )


# ============================================================
# FINAL OUTCOME
# ============================================================

can_record_final_outcome = (
    st.session_state[
        "proposal_submitted"
    ]
    or
    CURRENT_STAGE
    == "PROPOSAL_SUBMITTED"
)


if can_record_final_outcome:

    st.divider()

    st.subheader(
        "Final Customer Outcome"
    )


    st.caption(
        "Record the final outcome after "
        "the customer reviews the submitted proposal."
    )


    outcome_choice = st.radio(
        "Outcome",

        [
            "WON",
            "LOST",
        ],

        horizontal=True,

        key=
            f"final_outcome_{ACCOUNT_ID}",
    )


    if st.button(
        "Save Final Outcome",
        type="primary",
    ):

        try:
            send_core_event(
                account_id=ACCOUNT_ID,
                opportunity_id=OPPORTUNITY_ID,
                event_type="FINAL_OUTCOME",
                stage=outcome_choice,

                summary=(
                    f"{account.get('company')} "
                    f"opportunity outcome: "
                    f"{outcome_choice}."
                ),

                payload={
                    "outcome":
                        outcome_choice,

                    "approved_commercial_terms":
                        (
                            commercial_decision.get(
                                "final_terms"
                            )
                            if commercial_decision
                            else None
                        ),
                },
            )


            update_core_stage(
                account_id=ACCOUNT_ID,
                stage=outcome_choice,
                current_agent="COMPLETE",
                opportunity_id=OPPORTUNITY_ID,
            )


            st.session_state[
                "final_outcome"
            ] = outcome_choice


            st.success(
                f"Revenue journey completed: "
                f"{outcome_choice}"
            )


        except Exception as exc:
            st.error(
                f"Final outcome sync failed: {exc}"
            )


# ============================================================
# COMPLETE
# ============================================================

if st.session_state[
    "final_outcome"
]:

    st.success(
        "✓ Complete RevTrace Journey: "
        "Prospecting → Meeting → "
        "Deal Desk → Proposal / RFP → "
        f"{st.session_state['final_outcome']}"
    )