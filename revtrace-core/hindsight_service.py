from hindsight_client import Hindsight

from config import (
    HINDSIGHT_BASE_URL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_SHARED_BANK_ID,
)


client = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY,
    timeout=30.0,
)


def retain_journey_event(
    account_id,
    opportunity_id,
    company,
    agent,
    stage,
    event_type,
    summary,
    payload=None,
):
    content = (
        f"Account ID: {account_id}. "
        f"Company: {company}. "
        f"Agent: {agent}. "
        f"Stage: {stage}. "
        f"Event: {event_type}. "
        f"Summary: {summary}."
    )

    if payload:
        content += f" Additional context: {payload}."

    return client.retain(
        bank_id=HINDSIGHT_SHARED_BANK_ID,
        content=content,
        context="RevTrace end-to-end revenue journey",
        metadata={
            "account_id": account_id,
            "opportunity_id": opportunity_id or "",
            "company": company,
            "agent": agent,
            "stage": stage,
            "event_type": event_type,
        },
        document_id=(
            f"{account_id}-{agent}-{event_type}"
        ),
        retain_async=False,
    )

def recall_account_journey(
    account_id,
    company,
):
    query = (
        f"Recall the complete RevTrace revenue journey "
        f"for account {account_id}, company {company}. "
        f"Include prospecting, meetings, deal desk "
        f"decisions, proposals and final outcomes."
    )

    response = client.recall(
        bank_id=HINDSIGHT_SHARED_BANK_ID,
        query=query,
        budget="mid",
        max_tokens=3000,
    )

    results = []

    for item in response.results:

        metadata = (
            item.metadata
            or {}
        )

        # Only return memories explicitly
        # belonging to this account.
        if (
            metadata.get("account_id")
            != account_id
        ):
            continue

        results.append(
            {
                "id": item.id,
                "text": item.text,
                "metadata": metadata,
            }
        )

    return results