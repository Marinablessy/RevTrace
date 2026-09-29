from backend.hindsight_service import (
    recall_similar_prospects,
    filter_comparable_prospects,
    client,
)


try:
    raw_memories = recall_similar_prospects(
        industry="FinTech",
        role="CTO",
        company_size="Mid-Market",
        pain_point="High cloud infrastructure costs",
    )

    comparable = filter_comparable_prospects(
        raw_memories,
        industry="FinTech",
        role="CTO",
        company_size="Mid-Market",
    )

    print(
        f"Raw Hindsight memories returned: "
        f"{len(raw_memories)}"
    )

    print(
        f"Unique comparable prospects: "
        f"{len(comparable)}"
    )

    for index, prospect in enumerate(
        comparable,
        start=1,
    ):
        print(
            f"\n--- PROSPECT {index} ---"
        )

        print(
            "ID:",
            prospect["prospect_id"],
        )

        print(
            "Message angle:",
            prospect["message_angle"],
        )

        print(
            "Outcome:",
            prospect["outcome"],
        )

        print(
            "Memory:",
            prospect["representative_memory"],
        )

finally:
    client.close()