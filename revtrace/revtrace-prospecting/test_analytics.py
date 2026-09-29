from backend.hindsight_service import (
    recall_similar_prospects,
    filter_comparable_prospects,
    client,
)

from backend.analytics import analyze_prospects


try:
    memories = recall_similar_prospects(
        industry="FinTech",
        role="CTO",
        company_size="Mid-Market",
        pain_point="High cloud infrastructure costs",
    )

    prospects = filter_comparable_prospects(
        memories,
        industry="FinTech",
        role="CTO",
        company_size="Mid-Market",
    )

    result = analyze_prospects(prospects)

    print("\nRECOMMENDATION")
    print("----------------------------")

    print(
        "Recommended angle:",
        result["recommended_angle"],
    )

    print(
        "Confidence:",
        result["confidence"],
    )

    print(
        "Historical evidence:",
        result["evidence_count"],
    )

    print(
        "Historical success rate:",
        result["success_rate"],
    )

    print("\nALL STRATEGIES")
    print("----------------------------")

    for strategy in result["strategies"]:
        print(
            f"\nAngle: {strategy['angle']}"
        )
        print(
            f"Attempts: {strategy['attempts']}"
        )
        print(
            f"Positive outcomes: "
            f"{strategy['positive']}"
        )
        print(
            f"Success rate: "
            f"{strategy['success_rate']}"
        )
        print(
            f"Outcomes: "
            f"{strategy['outcomes']}"
        )

finally:
    client.close()