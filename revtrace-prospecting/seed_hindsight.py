import json

from backend.hindsight_service import (
    retain_prospect_memory,
    client,
)


def main():
    try:
        with open(
            "data/seed_prospects.json",
            "r",
            encoding="utf-8",
        ) as f:
            prospects = json.load(f)

        for prospect in prospects:
            print(
                f"Storing memory for "
                f"{prospect['prospect_id']}..."
            )

            retain_prospect_memory(
                prospect_id=prospect["prospect_id"],
                industry=prospect["industry"],
                role=prospect["role"],
                company_size=prospect["company_size"],
                pain_point=prospect["pain_point"],
                message_angle=prospect["message_angle"],
                outcome=prospect["outcome"],
            )

        print("Finished seeding Hindsight.")

    finally:
        client.close()


if __name__ == "__main__":
    main()