"""Entry point — submit a task and run builder → reviewer."""
import sys, json, uuid, asyncio
from pathlib import Path
from datetime import datetime
from agents import builder, reviewer, BUS


async def main(task: str, max_rounds: int = 3):
    packet_id = str(uuid.uuid4())[:8]
    packet    = {"id": packet_id, "task": task, "created_at": datetime.utcnow().isoformat()}

    inbox = BUS / f"inbox/builder/{packet_id}.json"
    inbox.write_text(json.dumps(packet, indent=2))
    print(f"Submitted: {packet_id}\nTask: {task}\n")

    for round_n in range(1, max_rounds + 1):
        print(f"--- Round {round_n} ---")
        review_path = await builder(inbox)
        result_path = await reviewer(review_path)

        result = json.loads(result_path.read_text())
        if result["review"]["verdict"] == "passed":
            print(f"\nPASSED in {round_n} round(s)")
            print(f"Result: {result_path}")
            print("\n=== Code ===")
            print(result["builder_result"]["code"])
            return

        print(f"Needs revision: {result['review']['feedback']}")
        # re-queue for next round
        task = f"{task}\n\nPrevious attempt feedback:\n{result['review']['feedback']}"
        packet["task"] = task
        inbox.write_text(json.dumps(packet, indent=2))

    print("Max rounds reached — check outbox for last result")


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "Build a FastAPI /health endpoint that returns uptime"
    asyncio.run(main(task))
