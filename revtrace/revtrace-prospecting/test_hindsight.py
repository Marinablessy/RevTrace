from hindsight_client import Hindsight

from backend.config import (
    HINDSIGHT_BASE_URL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_BANK_ID,
)

client = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY,
)

try:
    print("Connecting to:", HINDSIGHT_BASE_URL)

    print("\n1. Storing test memory...")

    client.retain(
        bank_id=HINDSIGHT_BANK_ID,
        content=(
            "A Mid-Market FinTech CTO with high cloud infrastructure "
            "costs received cost-efficiency outreach and booked a meeting."
        ),
    )

    print("SUCCESS: Memory stored")

    print("\n2. Recalling relevant memory...")

    result = client.recall(
        bank_id=HINDSIGHT_BANK_ID,
        query="What outreach strategy worked for a FinTech CTO?",
    )

    print("\nRECALLED MEMORIES:")

    if not result.results:
        print("No memories returned.")
    else:
        for index, memory in enumerate(result.results, start=1):
            print(f"\nMemory {index}:")
            print(memory.text)

finally:
    client.close()