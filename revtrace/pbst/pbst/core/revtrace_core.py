import requests

from config import REVTRACE_CORE_URL


def get_accounts():
    response = requests.get(
        f"{REVTRACE_CORE_URL}/accounts",
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if isinstance(data, list):
        return data

    return data.get(
        "accounts",
        [],
    )


def get_account(
    account_id: str
):
    response = requests.get(
        f"{REVTRACE_CORE_URL}/accounts/{account_id}",
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def get_account_memory(
    account_id: str
):
    response = requests.get(
        f"{REVTRACE_CORE_URL}/accounts/{account_id}/memory",
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_latest_commercial_decision(
    account_id: str
):
    data = get_account(
        account_id
    )

    events = data.get(
        "events",
        [],
    )

    for event in reversed(
        events
    ):
        if (
            event.get(
                "event_type"
            )
            == "COMMERCIAL_DECISION"
        ):
            payload = (
                event.get(
                    "payload"
                )
                or {}
            )

            return {
                "event_id":
                    event.get(
                        "event_id"
                    ),

                "stage":
                    event.get(
                        "stage"
                    ),

                "decision":
                    payload.get(
                        "decision"
                    ),

                "requested_terms":
                    payload.get(
                        "requestedTerms"
                    ),

                "final_terms":
                    payload.get(
                        "finalTerms"
                    ),

                "arr":
                    payload.get(
                        "arr"
                    ),

                "segment":
                    payload.get(
                        "segment"
                    ),

                "approver":
                    payload.get(
                        "approver"
                    ),

                "notes":
                    payload.get(
                        "notes"
                    ),
            }

    return None


def send_core_event(
    account_id: str,
    opportunity_id: str | None,
    event_type: str,
    stage: str,
    summary: str,
    payload: dict | None = None,
):
    response = requests.post(
        f"{REVTRACE_CORE_URL}/events",
        json={
            "account_id":
                account_id,

            "opportunity_id":
                opportunity_id,

            "agent":
                "PROPOSAL_RFP",

            "event_type":
                event_type,

            "stage":
                stage,

            "summary":
                summary,

            "payload":
                payload or {},
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def update_core_stage(
    account_id: str,
    stage: str,
    current_agent: str,
    opportunity_id: str | None = None,
):
    response = requests.post(
        f"{REVTRACE_CORE_URL}/accounts/{account_id}/stage",
        json={
            "stage":
                stage,

            "current_agent":
                current_agent,

            "opportunity_id":
                opportunity_id,
        },
        timeout=20,
    )

    response.raise_for_status()

    return response.json()