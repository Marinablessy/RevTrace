from backend.hindsight_service import (
    recall_similar_prospects,
    filter_comparable_prospects,
    client as hindsight_client,
)

from backend.analytics import analyze_prospects

from backend.llm_service import generate_outreach_message


try:
    prospect = {
        "name": "Arjun",
        "company": "NovaPay",
        "industry": "FinTech",
        "role": "CTO",
        "company_size": "Mid-Market",
        "pain_point": "High cloud infrastructure costs",
    }

    memories = recall_similar_prospects(
        industry=prospect["industry"],
        role=prospect["role"],
        company_size=prospect["company_size"],
        pain_point=prospect["pain_point"],
    )

    comparable = filter_comparable_prospects(
        memories,
        industry=prospect["industry"],
        role=prospect["role"],
        company_size=prospect["company_size"],
    )

    analysis = analyze_prospects(comparable)

    print("\nSTRATEGY")
    print("-------------------------")
    print("Recommended angle:", analysis["recommended_angle"])
    print("Confidence:", analysis["confidence"])
    print("Evidence:", analysis["evidence_count"])

    print("\nGENERATING MESSAGE...")

    message = generate_outreach_message(
        name=prospect["name"],
        company=prospect["company"],
        industry=prospect["industry"],
        role=prospect["role"],
        company_size=prospect["company_size"],
        pain_point=prospect["pain_point"],
        recommended_angle=analysis["recommended_angle"],
        memories=comparable,
    )

    print("\nGENERATED OUTREACH")
    print("-------------------------")
    print(message)

finally:
    hindsight_client.close()