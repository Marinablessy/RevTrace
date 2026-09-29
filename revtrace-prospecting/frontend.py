import requests
import streamlit as st

from datetime import date


# ============================================================
# SERVICES
# ============================================================

PROSPECT_API_URL = "http://127.0.0.1:8000"
CORE_URL = "http://127.0.0.1:8100"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="RevTrace Prospecting Agent",
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
    background: rgba(9,13,23,0.96);
}

.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1,
h2,
h3,
h4 {
    color: #f8fafc !important;
}

p,
label {
    color: #cbd5e1;
}

input,
textarea {
    background: #242833 !important;
    color: #ffffff !important;
}

div[data-baseweb="select"] > div {
    background: #242833;
    color: #ffffff;
}

div[data-testid="stMetric"] {
    background: #111827;
    border:
        1px solid
        rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 14px;
}

[data-testid="stExpander"] {
    background: #111827;
    border:
        1px solid
        rgba(255,255,255,0.08);
    border-radius: 12px;
}

button[kind="primary"] {
    border-radius: 10px;
}

hr {
    border-color:
        rgba(255,255,255,0.08);
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HTTP HELPERS
# ============================================================

def prospect_get(path):

    response = requests.get(
        f"{PROSPECT_API_URL}{path}",
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def prospect_post(
    path,
    payload=None,
):

    response = requests.post(
        f"{PROSPECT_API_URL}{path}",
        json=payload,
        timeout=90,
    )

    if not response.ok:

        try:
            detail = response.json()

        except Exception:
            detail = response.text

        raise RuntimeError(
            f"{response.status_code}: {detail}"
        )

    return response.json()


def core_get(path):

    response = requests.get(
        f"{CORE_URL}{path}",
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DISPLAY HELPERS
# ============================================================

def stage_label(value):

    if not value:
        return "Unknown"

    return (
        str(value)
        .replace("_", " ")
        .title()
    )


# ============================================================
# SESSION STATE
# ============================================================

def initialize_state():

    defaults = {
        "selected_account_id": "",
        "active_prospect_id": None,
        "analysis_result": None,
        "message_result": None,
        "outcome_result": None,
        "meeting_result": None,
        "completion_result": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


def clear_account_work():

    st.session_state[
        "analysis_result"
    ] = None

    st.session_state[
        "message_result"
    ] = None

    st.session_state[
        "outcome_result"
    ] = None

    st.session_state[
        "meeting_result"
    ] = None

    st.session_state[
        "completion_result"
    ] = None


initialize_state()


# ============================================================
# REVTRACE CORE HELPERS
# ============================================================

def load_core_accounts():

    data = core_get(
        "/accounts"
    )

    if isinstance(
        data,
        list,
    ):

        accounts = data

    else:

        accounts = data.get(
            "accounts",
            [],
        )


    return sorted(
        accounts,
        key=lambda item:
            item.get(
                "updated_at",
                item.get(
                    "created_at",
                    "",
                ),
            ),
        reverse=True,
    )


def load_core_account_detail(
    account_id
):

    return core_get(
        f"/accounts/{account_id}"
    )


def prospect_id_from_events(
    events
):

    for event in events:

        if (
            event.get(
                "event_type"
            )
            == "PROSPECT_CREATED"
        ):

            payload = (
                event.get(
                    "payload"
                )
                or {}
            )

            prospect_id = (
                payload.get(
                    "prospect_id"
                )
            )

            if prospect_id:

                return prospect_id

    return None


def build_account_workspace():

    accounts = (
        load_core_accounts()
    )

    workspace = []


    for account in accounts:

        account_id = (
            account.get(
                "account_id"
            )
        )

        if not account_id:
            continue


        try:

            detail = (
                load_core_account_detail(
                    account_id
                )
            )

            canonical_account = (
                detail.get(
                    "account",
                    account,
                )
            )

            events = (
                detail.get(
                    "events",
                    []
                )
            )

            prospect_id = (
                prospect_id_from_events(
                    events
                )
            )


            workspace.append(
                {
                    "account":
                        canonical_account,

                    "events":
                        events,

                    "prospect_id":
                        prospect_id,
                }
            )


        except Exception:

            workspace.append(
                {
                    "account":
                        account,

                    "events":
                        [],

                    "prospect_id":
                        None,
                }
            )


    return workspace


def find_account_for_prospect(
    prospect_id
):

    if not prospect_id:
        return None


    workspace = (
        build_account_workspace()
    )


    for item in workspace:

        if (
            item.get(
                "prospect_id"
            )
            == prospect_id
        ):

            return item

    return None


# ============================================================
# HEADER
# ============================================================

header_left, header_right = (
    st.columns(
        [5, 1]
    )
)


with header_left:

    st.caption(
        "REVTRACE • PROSPECTING INTELLIGENCE"
    )

    st.title(
        "Prospecting Agent"
    )

    st.caption(
        "Create a prospect, recall similar historical "
        "customer journeys with Hindsight, generate "
        "outreach and qualify the opportunity."
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
# CONNECTION STATUS
# ============================================================

connection_left, connection_right = (
    st.columns(2)
)


with connection_left:

    try:

        prospect_get(
            "/health"
        )

        st.success(
            "● Prospecting Backend Connected"
        )

    except Exception as exc:

        st.error(
            "Prospecting backend is not reachable."
        )

        st.code(
            str(exc)
        )

        st.stop()


with connection_right:

    try:

        load_core_accounts()

        st.success(
            "● RevTrace Core Connected"
        )

    except Exception as exc:

        st.error(
            "RevTrace Core is not reachable."
        )

        st.code(
            str(exc)
        )

        st.stop()


# ============================================================
# 1. NEW PROSPECT
# ============================================================

st.header(
    "1. New Prospect"
)


with st.form(
    "create_prospect_form",
    clear_on_submit=True,
):

    left, right = (
        st.columns(2)
    )


    with left:

        prospect_name = (
            st.text_input(
                "Prospect Name",
                value="",
                placeholder="Enter contact name",
            )
        )


        company = (
            st.text_input(
                "Company",
                value="",
                placeholder="Enter company name",
            )
        )


        industry = (
            st.text_input(
                "Industry",
                value="",
                placeholder=(
                    "Example: FinTech, SaaS, Healthcare"
                ),
            )
        )


    with right:

        role = (
            st.text_input(
                "Role",
                value="",
                placeholder=(
                    "Example: CTO, VP Engineering, CFO"
                ),
            )
        )


        company_size = (
            st.selectbox(
                "Company Size",

                [
                    "",
                    "Startup",
                    "SMB",
                    "Mid-Market",
                    "Enterprise",
                ],

                index=0,

                format_func=
                    lambda value:
                    (
                        "Select company size"
                        if value == ""
                        else value
                    ),
            )
        )


        pain_point = (
            st.text_area(
                "Pain Point",
                value="",
                placeholder=(
                    "Describe the prospect's main "
                    "business pain point"
                ),
                height=120,
            )
        )


    create_clicked = (
        st.form_submit_button(
            "Create Prospect",
            type="primary",
            use_container_width=True,
        )
    )


if create_clicked:

    missing = []


    if not prospect_name.strip():
        missing.append(
            "Prospect Name"
        )


    if not company.strip():
        missing.append(
            "Company"
        )


    if not industry.strip():
        missing.append(
            "Industry"
        )


    if not role.strip():
        missing.append(
            "Role"
        )


    if not company_size:
        missing.append(
            "Company Size"
        )


    if not pain_point.strip():
        missing.append(
            "Pain Point"
        )


    if missing:

        st.error(
            "Please complete: "
            + ", ".join(
                missing
            )
        )


    else:

        try:

            created = (
                prospect_post(
                    "/prospects",

                    {
                        "name":
                            prospect_name.strip(),

                        "company":
                            company.strip(),

                        "industry":
                            industry.strip(),

                        "role":
                            role.strip(),

                        "company_size":
                            company_size,

                        "pain_point":
                            pain_point.strip(),
                    },
                )
            )


            new_prospect_id = (
                created.get(
                    "prospect_id"
                )
            )


            st.session_state[
                "active_prospect_id"
            ] = (
                new_prospect_id
            )


            clear_account_work()


            matched = (
                find_account_for_prospect(
                    new_prospect_id
                )
            )


            if matched:

                new_account_id = (
                    matched[
                        "account"
                    ].get(
                        "account_id"
                    )
                )


                st.session_state[
                    "selected_account_id"
                ] = (
                    new_account_id
                )


                st.success(
                    f"Prospect created: "
                    f"{created.get('company')} "
                    f"→ {new_account_id}"
                )


            else:

                st.success(
                    f"Prospect created: "
                    f"{created.get('company')}"
                )

                st.info(
                    "RevTrace Core synchronization may "
                    "take a moment. Press Refresh if needed."
                )


            st.rerun()


        except Exception as exc:

            st.error(
                f"Prospect creation failed: {exc}"
            )


# ============================================================
# LOAD CANONICAL WORKSPACE
# ============================================================

try:

    workspace = (
        build_account_workspace()
    )


except Exception as exc:

    workspace = []

    st.error(
        f"Unable to load RevTrace accounts: {exc}"
    )


# ============================================================
# 2. PROSPECT WORKSPACE
# ============================================================

st.divider()


st.header(
    "2. Prospect Workspace"
)


if not workspace:

    st.info(
        "No customer accounts exist yet. "
        "Create a new prospect above."
    )


else:

    workspace_map = {
        item[
            "account"
        ][
            "account_id"
        ]:
            item

        for item
        in workspace

        if (
            item.get(
                "account"
            )
            and
            item[
                "account"
            ].get(
                "account_id"
            )
        )
    }


    account_ids = list(
        workspace_map.keys()
    )


    selector_options = (
        [""]
        +
        account_ids
    )


    saved_account_id = (
        st.session_state.get(
            "selected_account_id",
            "",
        )
    )


    if (
        saved_account_id
        in account_ids
    ):

        selected_index = (
            selector_options.index(
                saved_account_id
            )
        )

    else:

        selected_index = 0


    chosen_account_id = (
        st.selectbox(
            "Select RevTrace Account",

            options=
                selector_options,

            index=
                selected_index,

            format_func=
                lambda account_id:
                (
                    "Select an account"
                    if account_id == ""
                    else
                    (
                        f"{workspace_map[account_id]['account'].get('company', 'Unknown')} "
                        f"— "
                        f"{stage_label(workspace_map[account_id]['account'].get('stage'))}"
                    )
                ),
        )
    )


    # ========================================================
    # NOTHING SELECTED
    # ========================================================

    if not chosen_account_id:

        if (
            st.session_state.get(
                "selected_account_id"
            )
        ):

            st.session_state[
                "selected_account_id"
            ] = ""

            st.session_state[
                "active_prospect_id"
            ] = None

            clear_account_work()


        st.info(
            "No account selected. "
            "Create a new prospect above or "
            "choose an account from the dropdown."
        )


    # ========================================================
    # ACCOUNT SELECTED
    # ========================================================

    else:

        previous_account_id = (
            st.session_state.get(
                "selected_account_id"
            )
        )


        if (
            previous_account_id
            != chosen_account_id
        ):

            clear_account_work()


        st.session_state[
            "selected_account_id"
        ] = (
            chosen_account_id
        )


        selected_workspace = (
            workspace_map[
                chosen_account_id
            ]
        )


        account = (
            selected_workspace[
                "account"
            ]
        )


        events = (
            selected_workspace.get(
                "events",
                []
            )
        )


        prospect_id = (
            selected_workspace.get(
                "prospect_id"
            )
        )


        st.session_state[
            "active_prospect_id"
        ] = (
            prospect_id
        )


        # ====================================================
        # ACCOUNT SUMMARY
        # ====================================================

        c1, c2, c3, c4, c5 = (
            st.columns(5)
        )


        with c1:

            st.metric(
                "Company",

                account.get(
                    "company",
                    "—",
                ),
            )


        with c2:

            st.metric(
                "Contact",

                account.get(
                    "contact_name",
                    "—",
                ),
            )


        with c3:

            st.metric(
                "Industry",

                account.get(
                    "industry",
                    "—",
                ),
            )


        with c4:

            st.metric(
                "Role",

                account.get(
                    "role",
                    "—",
                ),
            )


        with c5:

            st.metric(
                "Stage",

                stage_label(
                    account.get(
                        "stage"
                    )
                ),
            )


        info_left, info_right = (
            st.columns(2)
        )


        with info_left:

            st.caption(
                "Account ID"
            )

            st.write(
                account.get(
                    "account_id",
                    "—",
                )
            )


        with info_right:

            st.caption(
                "Opportunity ID"
            )

            st.write(
                account.get(
                    "opportunity_id"
                )
                or
                "Not created yet"
            )


        # ====================================================
        # ORIGINAL PROSPECT CONTEXT
        # ====================================================

        created_event = (
            next(
                (
                    event
                    for event
                    in events

                    if (
                        event.get(
                            "event_type"
                        )
                        == "PROSPECT_CREATED"
                    )
                ),
                None,
            )
        )


        created_payload = (
            (
                created_event.get(
                    "payload"
                )
                or {}
            )
            if created_event
            else {}
        )


        st.caption(
            "Pain Point"
        )


        st.write(
            created_payload.get(
                "pain_point"
            )
            or
            "Not available"
        )


        core_stage = (
            account.get(
                "stage"
            )
        )


        current_agent = (
            account.get(
                "current_agent"
            )
        )


        # ====================================================
        # HAS THIS ACCOUNT LEFT PROSPECTING?
        # ====================================================

        has_left_prospecting = (
            current_agent
            != "PROSPECTING"
            or
            core_stage
            in {
                "DEAL_DESK",
                "COMMERCIAL_APPROVED",
                "PROPOSAL_DRAFT",
                "PROPOSAL_SUBMITTED",
                "WON",
                "LOST",
            }
        )


        # ====================================================
        # COMPLETED / HANDED-OFF ACCOUNT
        # ====================================================

        if has_left_prospecting:

            st.divider()


            st.subheader(
                "Prospecting Status"
            )


            if (
                core_stage
                == "WON"
            ):

                st.success(
                    "✓ Prospecting completed. "
                    "This customer journey has reached WON."
                )


            elif (
                core_stage
                == "LOST"
            ):

                st.error(
                    "Prospecting completed. "
                    "This customer journey has reached LOST."
                )


            else:

                st.success(
                    f"✓ Prospecting completed. "
                    f"This account is currently at "
                    f"{stage_label(core_stage)} "
                    f"with "
                    f"{stage_label(current_agent)}."
                )


            st.caption(
                "Prospecting actions are read-only because "
                "ownership has already moved to another "
                "RevTrace agent."
            )


        # ====================================================
        # NO PROSPECT MAPPING
        # ====================================================

        elif not prospect_id:

            st.warning(
                "This account does not contain a "
                "Prospecting prospect ID mapping, so "
                "Prospecting actions cannot be performed."
            )


        # ====================================================
        # ACTIVE PROSPECTING ACCOUNT
        # ====================================================

        else:

            try:

                local_prospect = (
                    prospect_get(
                        f"/prospects/{prospect_id}"
                    )
                )


            except Exception as exc:

                local_prospect = None

                st.error(
                    f"Could not load the local "
                    f"Prospecting record: {exc}"
                )


            if local_prospect:

                # ============================================
                # 3. HINDSIGHT ANALYSIS
                # ============================================

                st.divider()


                st.header(
                    "3. Hindsight Prospect Analysis"
                )


                st.caption(
                    "Recall similar historical customer "
                    "journeys before choosing an outreach angle."
                )


                if st.button(
                    "Recall Similar Prospects",

                    type="primary",

                    key=
                        f"recall_{chosen_account_id}",
                ):

                    try:

                        with st.spinner(
                            "Recalling similar prospects "
                            "from Hindsight..."
                        ):

                            analysis_result = (
                                prospect_post(
                                    f"/prospects/"
                                    f"{prospect_id}"
                                    f"/analyze"
                                )
                            )


                        st.session_state[
                            "analysis_result"
                        ] = (
                            analysis_result
                        )


                        st.success(
                            "Hindsight recall completed."
                        )


                    except Exception as exc:

                        st.error(
                            f"Analysis failed: {exc}"
                        )


                analysis_result = (
                    st.session_state.get(
                        "analysis_result"
                    )
                )


                if analysis_result:

                    memory_result = (
                        analysis_result.get(
                            "memory",
                            {}
                        )
                    )


                    analysis = (
                        analysis_result.get(
                            "analysis",
                            {}
                        )
                    )


                    m1, m2, m3, m4 = (
                        st.columns(4)
                    )


                    with m1:

                        st.metric(
                            "Memory Provider",

                            memory_result.get(
                                "provider",
                                "Hindsight",
                            ),
                        )


                    with m2:

                        st.metric(
                            "Raw Memories",

                            memory_result.get(
                                "raw_memories_recalled",
                                0,
                            ),
                        )


                    with m3:

                        st.metric(
                            "Comparable Prospects",

                            memory_result.get(
                                "comparable_prospects",
                                0,
                            ),
                        )


                    with m4:

                        st.metric(
                            "Recommended Angle",

                            analysis.get(
                                "recommended_angle",
                                "Unknown",
                            ),
                        )


                    if analysis.get(
                        "confidence"
                    ):

                        st.write(
                            "**Confidence:**",
                            analysis.get(
                                "confidence"
                            ),
                        )


                    comparable = (
                        analysis_result.get(
                            "comparable_prospects",
                            []
                        )
                    )


                    if comparable:

                        with st.expander(
                            "View recalled comparable prospects"
                        ):

                            st.json(
                                comparable
                            )


                # ============================================
                # 4. GENERATE OUTREACH
                # ============================================

                st.divider()


                st.header(
                    "4. Generate Outreach"
                )


                if st.button(
                    "Generate Personalized Outreach",

                    type="primary",

                    key=
                        f"generate_{chosen_account_id}",
                ):

                    try:

                        with st.spinner(
                            "Generating personalized outreach..."
                        ):

                            generated = (
                                prospect_post(
                                    f"/prospects/"
                                    f"{prospect_id}"
                                    f"/generate-message"
                                )
                            )


                        st.session_state[
                            "message_result"
                        ] = generated


                        st.success(
                            "Outreach generated."
                        )


                    except Exception as exc:

                        st.error(
                            f"Message generation failed: {exc}"
                        )


                message_result = (
                    st.session_state.get(
                        "message_result"
                    )
                )


                if message_result:

                    g1, g2, g3 = (
                        st.columns(3)
                    )


                    with g1:

                        st.metric(
                            "Message Angle",

                            message_result.get(
                                "recommended_angle",
                                "Unknown",
                            ),
                        )


                    with g2:

                        st.metric(
                            "Confidence",

                            message_result.get(
                                "confidence",
                                "Unknown",
                            ),
                        )


                    with g3:

                        st.metric(
                            "Evidence Count",

                            message_result.get(
                                "evidence_count",
                                0,
                            ),
                        )


                    st.subheader(
                        "Generated Message"
                    )


                    st.markdown(
                        message_result.get(
                            "message",
                            "No message returned.",
                        )
                    )


                # ============================================
                # 5. OUTREACH OUTCOME
                # ============================================

                st.divider()


                st.header(
                    "5. Outreach Outcome"
                )


                outcome = (
                    st.selectbox(
                        "Record Outcome",

                        [
                            "",
                            "NO_RESPONSE",
                            "REPLIED",
                            "MEETING_BOOKED",
                            "QUALIFIED",
                            "CONVERTED_TO_DEAL",
                        ],

                        index=0,

                        key=
                            f"outcome_{chosen_account_id}",

                        format_func=
                            lambda value:
                            (
                                "Select outcome"
                                if value == ""
                                else stage_label(
                                    value
                                )
                            ),
                    )
                )


                if st.button(
                    "Save Outcome",

                    disabled=
                        not outcome,

                    key=
                        f"save_outcome_{chosen_account_id}",
                ):

                    try:

                        saved_outcome = (
                            prospect_post(
                                f"/prospects/"
                                f"{prospect_id}"
                                f"/outcome",

                                {
                                    "outcome":
                                        outcome
                                },
                            )
                        )


                        st.session_state[
                            "outcome_result"
                        ] = (
                            saved_outcome
                        )


                        st.success(
                            f"Outcome saved: "
                            f"{stage_label(outcome)}"
                        )


                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Outcome save failed: {exc}"
                        )


                # ============================================
                # REFRESH PROSPECT
                # ============================================

                try:

                    local_prospect = (
                        prospect_get(
                            f"/prospects/{prospect_id}"
                        )
                    )

                except Exception:

                    pass


                local_stage = (
                    local_prospect.get(
                        "stage"
                    )
                )


                # ============================================
                # 6. DISCOVERY MEETING
                # ============================================

                st.divider()


                st.header(
                    "6. Discovery Meeting"
                )


                meeting_allowed = (
                    local_stage
                    in {
                        "OUTREACH_SENT",
                        "ENGAGED_PROSPECT",
                        "MEETING_SCHEDULED",
                    }
                )


                if not meeting_allowed:

                    st.info(
                        f"Meeting actions are unavailable. "
                        f"Current stage: "
                        f"{stage_label(local_stage)}"
                    )


                meeting_left, meeting_right = (
                    st.columns(2)
                )


                with meeting_left:

                    meeting_date = (
                        st.date_input(
                            "Meeting Date",

                            value=
                                date.today(),

                            disabled=
                                not meeting_allowed,

                            key=
                                f"meeting_date_"
                                f"{chosen_account_id}",
                        )
                    )


                with meeting_right:

                    meeting_time = (
                        st.time_input(
                            "Meeting Time",

                            disabled=
                                not meeting_allowed,

                            key=
                                f"meeting_time_"
                                f"{chosen_account_id}",
                        )
                    )


                if st.button(
                    "Schedule Meeting",

                    disabled=
                        not meeting_allowed,

                    key=
                        f"schedule_"
                        f"{chosen_account_id}",
                ):

                    try:

                        meeting_result = (
                            prospect_post(
                                f"/prospects/"
                                f"{prospect_id}"
                                f"/schedule-meeting",

                                {
                                    "meeting_date":
                                        str(
                                            meeting_date
                                        ),

                                    "meeting_time":
                                        meeting_time.strftime(
                                            "%H:%M"
                                        ),
                                },
                            )
                        )


                        st.session_state[
                            "meeting_result"
                        ] = (
                            meeting_result
                        )


                        st.success(
                            "Meeting scheduled."
                        )


                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Meeting scheduling failed: {exc}"
                        )


                # ============================================
                # REFRESH MEETING STATUS
                # ============================================

                try:

                    local_prospect = (
                        prospect_get(
                            f"/prospects/{prospect_id}"
                        )
                    )

                except Exception:

                    pass


                meeting_status = (
                    local_prospect.get(
                        "meeting_status"
                    )
                )


                if meeting_status:

                    st.write(
                        "**Meeting Status:**",
                        stage_label(
                            meeting_status
                        ),
                    )


                if local_prospect.get(
                    "meeting_date"
                ):

                    st.write(
                        "**Scheduled:**",

                        local_prospect.get(
                            "meeting_date"
                        ),

                        local_prospect.get(
                            "meeting_time",
                            "",
                        ),
                    )


                complete_allowed = (
                    meeting_status
                    == "SCHEDULED"
                )


                if st.button(
                    "Complete Meeting & Qualify Opportunity",

                    type="primary",

                    disabled=
                        not complete_allowed,

                    key=
                        f"complete_"
                        f"{chosen_account_id}",
                ):

                    try:

                        completion = (
                            prospect_post(
                                f"/prospects/"
                                f"{prospect_id}"
                                f"/complete-meeting"
                            )
                        )


                        st.session_state[
                            "completion_result"
                        ] = (
                            completion
                        )


                        st.success(
                            "Meeting completed. "
                            "The prospect is now a "
                            "qualified opportunity."
                        )


                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Meeting completion failed: {exc}"
                        )


                # ============================================
                # 7. HANDOFF
                # ============================================

                st.divider()


                st.header(
                    "7. RevTrace Handoff"
                )


                try:

                    refreshed_core = (
                        load_core_account_detail(
                            chosen_account_id
                        )
                    )

                    refreshed_account = (
                        refreshed_core.get(
                            "account",
                            account,
                        )
                    )


                except Exception:

                    refreshed_account = account


                refreshed_stage = (
                    refreshed_account.get(
                        "stage"
                    )
                )


                if (
                    refreshed_stage
                    == "QUALIFIED_OPPORTUNITY"
                ):

                    st.success(
                        "✓ Qualified Opportunity"
                    )

                    st.write(
                        "Prospecting is complete. "
                        "The account is ready for Deal Desk."
                    )


                elif (
                    refreshed_stage
                    == "MEETING_SCHEDULED"
                ):

                    st.info(
                        "Discovery meeting scheduled."
                    )


                elif (
                    refreshed_stage
                    == "ENGAGED_PROSPECT"
                ):

                    st.info(
                        "Customer engaged. "
                        "Continue to discovery meeting."
                    )


                elif (
                    refreshed_stage
                    == "OUTREACH_SENT"
                ):

                    st.info(
                        "Outreach sent. "
                        "Waiting for customer response."
                    )


                else:

                    st.info(
                        f"Current stage: "
                        f"{stage_label(refreshed_stage)}"
                    )