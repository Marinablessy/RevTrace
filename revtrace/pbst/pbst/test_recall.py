from core.hindsight_memory import HindsightMemory

memory = HindsightMemory()

print("Searching Hindsight...")

results = memory.recall(
    "What capabilities did our organization demonstrate "
    "in previous mining proposals?"
)

print("\nRESULTS:\n")

for i, result in enumerate(results, 1):
    print(f"--- Result {i} ---")
    print(result.get("text", ""))
    print()