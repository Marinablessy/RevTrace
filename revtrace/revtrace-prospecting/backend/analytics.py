from collections import defaultdict


POSITIVE_OUTCOMES = {
    "REPLIED",
    "MEETING_BOOKED",
    "QUALIFIED",
    "CONVERTED_TO_DEAL",
}


def analyze_prospects(prospects: list[dict]):
    stats = defaultdict(
        lambda: {
            "attempts": 0,
            "positive": 0,
            "outcomes": [],
        }
    )

    for prospect in prospects:
        angle = prospect.get("message_angle")
        outcome = prospect.get("outcome")

        if not angle:
            continue

        stats[angle]["attempts"] += 1
        stats[angle]["outcomes"].append(outcome)

        if outcome in POSITIVE_OUTCOMES:
            stats[angle]["positive"] += 1

    ranked = []

    for angle, values in stats.items():
        attempts = values["attempts"]
        positive = values["positive"]

        success_rate = (
            positive / attempts
            if attempts > 0
            else 0
        )

        ranked.append(
            {
                "angle": angle,
                "attempts": attempts,
                "positive": positive,
                "success_rate": round(
                    success_rate,
                    2,
                ),
                "outcomes": values["outcomes"],
            }
        )

    ranked.sort(
        key=lambda x: (
            x["success_rate"],
            x["attempts"],
        ),
        reverse=True,
    )

    if not ranked:
        return {
            "recommended_angle": None,
            "confidence": "LOW",
            "evidence_count": 0,
            "success_rate": 0,
            "strategies": [],
        }

    winner = ranked[0]

    evidence_count = winner["attempts"]

    if evidence_count >= 7:
        confidence = "HIGH"
    elif evidence_count >= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return {
        "recommended_angle": winner["angle"],
        "confidence": confidence,
        "evidence_count": evidence_count,
        "success_rate": winner["success_rate"],
        "strategies": ranked,
    }