#!/usr/bin/env python3
"""
create_agents.py — One-click setup for memspren-heavy and memspren-light agents.

Runs `openclaw agents add` for each agent. OpenClaw will open an interactive
panel for each — set the model and confirm before this script continues.

Usage:
    python scripts/create_agents.py
"""

import subprocess
import sys

AGENTS = [
    {
        "id": "memspren-heavy",
        "role": "Extraction, insights, entity plan",
        "suggested_model": "claude-sonnet-4-6 or claude-opus-4-6",
    },
    {
        "id": "memspren-light",
        "role": "Goals, tasks, hot-memory, content, linking",
        "suggested_model": "claude-haiku-4-5 or claude-sonnet-4-6",
    },
]


def add_agent(agent: dict) -> bool:
    print(f"\nAdding agent: {agent['id']}")
    print(f"  Role:            {agent['role']}")
    print(f"  Suggested model: {agent['suggested_model']}")
    print("  OpenClaw will open a panel — select your model and confirm.")
    try:
        result = subprocess.run(
            ["openclaw", "agents", "add", agent["id"]],
            check=False,
        )
        if result.returncode != 0:
            print(f"  Warning: openclaw exited with code {result.returncode}", file=sys.stderr)
            return False
        return True
    except FileNotFoundError:
        print("  Error: `openclaw` command not found. Is OpenClaw installed and in PATH?", file=sys.stderr)
        return False


def main():
    print("memspren agent setup")
    print("=" * 40)
    print("This will add two agents to OpenClaw.")
    print("Each step opens an interactive panel — set the model and confirm before continuing.")

    results = []
    for agent in AGENTS:
        ok = add_agent(agent)
        results.append((agent["id"], ok))

    print("\n" + "=" * 40)
    print("Results:")
    all_ok = True
    for agent_id, ok in results:
        status = "OK" if ok else "FAILED"
        print(f"  {agent_id}: {status}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\nDone. Both agents added.")
        print("If you need to change the model later, use: openclaw agents edit <id>")
    else:
        print("\nSome agents could not be added. Run `openclaw agents add <id>` manually.")
        sys.exit(1)


if __name__ == "__main__":
    main()
