from backend.hindsight_service import client
from backend.config import HINDSIGHT_BANK_ID

try:
    bank = client.create_bank(
        bank_id=HINDSIGHT_BANK_ID,
        name="RevTrace Sales Memory"
    )

    print("SUCCESS: Memory bank created")
    print(bank)

except Exception as e:
    print("ERROR:", e)

finally:
    client.close()