"""
Multi-pass executor — understand -> plan -> execute state machine.
Each phase calls the LLM once; state is persisted between runs via JSON.
Run: pip install -r requirements.txt && python main.py "build a CLI password generator in Python"
"""
import os, sys, json, time
from pathlib import Path
from openai import OpenAI

MINIMAX_KEY = os.environ["MINIMAX_API_KEY"]
BASE_URL    = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")
STATE_FILE  = Path("state.json")

ai = OpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)

PHASES = ["understand", "plan", "execute"]


# --- LLM helpers ---

def call(system: str, user: str) -> str:
    resp = ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return resp.choices[0].message.content


def phase_understand(task: str) -> str:
    return call(
        "You are a senior engineer decomposing a task. "
        "Identify: (1) what must be built, (2) constraints, (3) ambiguities. "
        "Be concise and structured.",
        f"Task: {task}",
    )


def phase_plan(task: str, understanding: str) -> str:
    return call(
        "You are a senior engineer creating an implementation plan. "
        "Given the task understanding, produce a numbered step-by-step plan. "
        "Each step must be concrete and independently executable.",
        f"Task: {task}\n\nUnderstanding:\n{understanding}",
    )


def phase_execute(task: str, understanding: str, plan: str) -> str:
    return call(
        "You are a senior engineer executing a plan. "
        "Produce the final deliverable: working code, config, or documentation. "
        "Follow the plan exactly. Output only the deliverable, no commentary.",
        f"Task: {task}\n\nUnderstanding:\n{understanding}\n\nPlan:\n{plan}",
    )


# --- State machine ---

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def run(task: str):
    state = load_state()

    # Allow resuming with a different task
    if state.get("task") and state["task"] != task:
        print(f"[resume] Resuming previous task: {state['task']}")
        task = state["task"]
    else:
        state["task"] = task

    for phase in PHASES:
        if phase in state.get("completed", []):
            print(f"[skip]  {phase} already done")
            continue

        print(f"\n[{phase.upper()}] Running...", flush=True)
        t0 = time.time()

        if phase == "understand":
            result = phase_understand(task)
        elif phase == "plan":
            result = phase_plan(task, state["understand"])
        else:
            result = phase_execute(task, state["understand"], state["plan"])

        elapsed = time.time() - t0
        state[phase] = result
        state.setdefault("completed", []).append(phase)
        save_state(state)

        print(f"[{phase.upper()}] done in {elapsed:.1f}s")
        print("-" * 60)
        print(result)

    print("\n[DONE] All phases complete. State saved to state.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if STATE_FILE.exists():
            state = load_state()
            remaining = [p for p in PHASES if p not in state.get("completed", [])]
            if remaining:
                print(f"Resuming task: {state['task']}")
                run(state["task"])
            else:
                print("All phases already complete. Delete state.json to restart.")
        else:
            raise SystemExit('Usage: python main.py "your task description"')
    else:
        run(" ".join(sys.argv[1:]))
