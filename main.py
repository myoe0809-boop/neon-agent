
import os
import json
from datetime import datetime, timezone
from groq import Groq

MODEL = "llama-3.3-70b-versatile"
STATE_FILE = "neon_state.json"

SYSTEM_PROMPT = """
You are NEON, an autonomous but cautious digital business research agent.

Goal:
Find realistic, legal ways to build recurring digital revenue with zero initial investment.

Rules:
- Never spend money or activate paid services.
- Never publish, sell, contact customers, create accounts, or make commitments.
- Never claim revenue that has not actually happened.
- Prefer digital products and small software tools that require little customer support.
- Evaluate ideas based on demand, competition, production effort, and realistic pricing.
- Create useful drafts and save them for human review.
- Clearly distinguish facts, assumptions, and estimates.
- Work in Korean.
"""

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"runs": 0, "history": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY secret is missing.")

    client = Groq(api_key=api_key)
    state = load_state()

    prompt = f"""
    Previous completed runs: {state['runs']}
    Previous ideas:
    {json.dumps(state['history'][-5:], ensure_ascii=False)}

    Perform today's business research.

    Return:
    1. Three realistic zero-cost digital business opportunities.
    2. A comparison of demand, competition, effort, and risks.
    3. Select the best opportunity and explain why.
    4. Create one concrete draft deliverable for that opportunity.
    5. List the exact human approval steps required before publication or sale.

    Do not invent market research or claim to have published anything.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    report = response.choices[0].message.content or "No response generated."

    state["runs"] += 1
    state["history"].append({
        "date": datetime.now(timezone.utc).isoformat(),
        "report": report
    })
    save_state(state)

    os.makedirs("reports", exist_ok=True)
    filename = datetime.now(timezone.utc).strftime("reports/report_%Y%m%d_%H%M%S.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# NEON Business Report\n\n")
        f.write(report)

    print(report)
    print(f"\nSaved report: {filename}")

if __name__ == "__main__":
    main()
