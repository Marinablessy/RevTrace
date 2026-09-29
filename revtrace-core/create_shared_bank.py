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


try:
    result = client.create_bank(
        bank_id=HINDSIGHT_SHARED_BANK_ID,
        name="RevTrace Shared Revenue Memory",
    )

    print("Shared Hindsight bank created:")
    print(result)

except Exception as exc:
    print("Bank creation response:")
    print(exc)