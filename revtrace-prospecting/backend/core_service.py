import requests

from backend.config import REVTRACE_CORE_URL


def create_core_account(
    company,
    contact_name,
    industry,
    role,
):
    response = requests.post(
        f"{REVTRACE_CORE_URL}/accounts",
        json={
            "company": company,
            "contact_name": contact_name,
            "industry": industry,
            "role": role,
        },
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


def send_core_event(
    account_id,
    opportunity_id,
    event_type,
    stage,
    summary,
    payload=None,
):
    response = requests.post(
        f"{REVTRACE_CORE_URL}/events",
        json={
            "account_id": account_id,
            "opportunity_id": opportunity_id,
            "agent": "PROSPECTING",
            "event_type": event_type,
            "stage": stage,
            "summary": summary,
            "payload": payload or {},
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def update_core_stage(
    account_id,
    stage,
    current_agent,
    opportunity_id=None,
):
    response = requests.post(
        (
            f"{REVTRACE_CORE_URL}"
            f"/accounts/{account_id}/stage"
        ),
        json={
            "stage": stage,
            "current_agent": current_agent,
            "opportunity_id": opportunity_id,
        },
        timeout=20,
    )

    response.raise_for_status()

    return response.json()