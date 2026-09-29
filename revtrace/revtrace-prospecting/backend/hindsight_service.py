from hindsight_client import Hindsight

from backend.config import (
    HINDSIGHT_BASE_URL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_BANK_ID,
)


client = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY,
    timeout=30.0,
)


def retain_prospect_memory(
    prospect_id: str,
    industry: str,
    role: str,
    company_size: str,
    pain_point: str,
    message_angle: str,
    outcome: str,
):

    content = (
        f"Prospect ID: {prospect_id}. "
        f"Industry: {industry}. "
        f"Role: {role}. "
        f"Company size: "
        f"{company_size}. "
        f"Pain point: "
        f"{pain_point}. "
        f"Message angle: "
        f"{message_angle}. "
        f"Outcome: {outcome}."
    )

    client.retain(
        bank_id=HINDSIGHT_BANK_ID,
        content=content,
        context=(
            "RevTrace outbound "
            "prospecting experience"
        ),
        metadata={
            "prospect_id":
                prospect_id,

            "industry":
                industry,

            "role":
                role,

            "company_size":
                company_size,

            "message_angle":
                message_angle,

            "outcome":
                outcome,
        },
        document_id=(
            f"prospect-{prospect_id}"
        ),
        retain_async=False,
    )


def recall_similar_prospects(
    industry: str,
    role: str,
    company_size: str,
    pain_point: str,
):

    query = (
        "Find previous outbound "
        "prospecting experiences "
        "relevant to a "
        f"{company_size} "
        f"{industry} company where "
        f"the prospect role is "
        f"{role} and the pain point "
        f"is {pain_point}. "
        "Prioritize similar "
        "prospects and outreach "
        "outcomes."
    )

    response = client.recall(
        bank_id=
            HINDSIGHT_BANK_ID,
        query=query,
        budget="mid",
        max_tokens=2500,
    )

    results = []

    for item in response.results:
        results.append(
            {
                "id": item.id,
                "text": item.text,
                "metadata":
                    item.metadata or {},
                "document_id":
                    getattr(
                        item,
                        "document_id",
                        None,
                    ),
            }
        )

    return results


def filter_comparable_prospects(
    memories: list[dict],
    industry: str,
    role: str,
    company_size: str,
):

    comparable = {}

    for memory in memories:

        metadata = memory.get(
            "metadata",
            {},
        )

        memory_industry = (
            metadata.get(
                "industry",
                "",
            )
        )

        memory_role = (
            metadata.get(
                "role",
                "",
            )
        )

        memory_company_size = (
            metadata.get(
                "company_size",
                "",
            )
        )

        if (
            memory_industry.lower()
            != industry.lower()
        ):
            continue

        if (
            memory_role.lower()
            != role.lower()
        ):
            continue

        if (
            memory_company_size.lower()
            != company_size.lower()
        ):
            continue

        prospect_id = metadata.get(
            "prospect_id"
        )

        if not prospect_id:
            continue

        comparable[
            prospect_id
        ] = {
            "prospect_id":
                prospect_id,

            "industry":
                memory_industry,

            "role":
                memory_role,

            "company_size":
                memory_company_size,

            "message_angle":
                metadata.get(
                    "message_angle"
                ),

            "outcome":
                metadata.get(
                    "outcome"
                ),

            "representative_memory":
                memory["text"],
        }

    return list(
        comparable.values()
    )