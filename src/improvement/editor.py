import json
import os
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL, EDIT_MEMORY_PATH

client = Groq(api_key=GROQ_API_KEY)


def load_edit_memory() -> list:
    """Load existing style rules from memory file."""
    if os.path.exists(EDIT_MEMORY_PATH):
        with open(EDIT_MEMORY_PATH, "r") as f:
            data = json.load(f)
            return data.get("style_rules", [])
    return []


def save_edit_memory(style_rules: list):
    """Save updated style rules to memory file."""
    with open(EDIT_MEMORY_PATH, "w") as f:
        json.dump({"style_rules": style_rules}, f, indent=2)
    print(f"[Editor] Saved {len(style_rules)} style rules to memory.")


def extract_rules_from_edit(original_draft: str, edited_draft: str) -> list:
    """
    Use Groq to analyze the diff between original and edited draft
    and extract reusable style/content rules.
    """
    print("[Editor] Analyzing operator edits to extract rules...")

    prompt = f"""An operator reviewed an AI-generated legal case fact summary and edited it.
Your job is to compare the original and edited versions and extract reusable rules that should apply to ALL future drafts.

ORIGINAL DRAFT:
{original_draft}

EDITED DRAFT:
{edited_draft}

Analyze what changed and why. Extract 2-5 concrete, reusable rules that capture the operator's preferences.
Rules should be specific and actionable, not vague.

Examples of good rules:
- "Always include the full property address in the Overview section"
- "Use passive voice when describing findings"
- "List all monetary amounts in a dedicated Facts section"
- "Flag any missing signatures explicitly"

Respond ONLY with a JSON array of rule strings. No explanation, no markdown, just the JSON array.
Example: ["rule 1", "rule 2", "rule 3"]"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500
    )

    raw = response.choices[0].message.content.strip()

    try:
        # Clean up response in case of markdown
        raw = raw.replace("```json", "").replace("```", "").strip()
        new_rules = json.loads(raw)
        print(f"[Editor] Extracted {len(new_rules)} new rules.")
        return new_rules
    except json.JSONDecodeError:
        print("[Editor] Could not parse rules. Skipping.")
        return []


def process_operator_edit(original_draft: str, edited_draft: str) -> list:
    """
    Full improvement loop:
    1. Extract rules from the edit
    2. Merge with existing rules (avoid duplicates)
    3. Save updated memory
    4. Return all current rules
    """
    existing_rules = load_edit_memory()
    new_rules = extract_rules_from_edit(original_draft, edited_draft)

    # Merge without duplicates
    all_rules = list(existing_rules)
    for rule in new_rules:
        if rule not in all_rules:
            all_rules.append(rule)

    save_edit_memory(all_rules)
    print(f"[Editor] Total rules in memory: {len(all_rules)}")
    return all_rules