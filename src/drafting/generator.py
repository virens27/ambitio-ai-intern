from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL


client = Groq(api_key=GROQ_API_KEY)


def build_prompt(evidence: str, doc_name: str, style_rules: list = None) -> str:
    """Build the prompt for draft generation."""
    rules_section = ""
    if style_rules:
        rules_text = "\n".join(f"- {rule}" for rule in style_rules)
        rules_section = f"""
OPERATOR STYLE PREFERENCES (learned from past edits — follow these):
{rules_text}
"""

    return f"""You are a legal document analyst. Your job is to generate a grounded case fact summary based ONLY on the evidence provided below.

DOCUMENT: {doc_name}
{rules_section}
RETRIEVED EVIDENCE:
{evidence}

INSTRUCTIONS:
- Write a structured case fact summary using ONLY the evidence above
- Do NOT add any information not present in the evidence
- Use these sections: Overview, Key Parties, Key Dates & Events, Critical Facts, Flags & Concerns
- If a section has no evidence, write "No information found in source document"
- Be concise and factual

CASE FACT SUMMARY:"""


def generate_draft(evidence: str, doc_name: str, style_rules: list = None) -> dict:
    """
    Generate a grounded draft using Groq LLM.
    Returns the draft text and the prompt used.
    """
    print(f"[Generator] Generating draft for: {doc_name}")

    prompt = build_prompt(evidence, doc_name, style_rules)

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise legal document analyst. Always ground your output strictly in provided evidence. Never hallucinate or assume facts."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1500
    )

    draft_text = response.choices[0].message.content.strip()

    print(f"[Generator] Draft generated. Length: {len(draft_text)} chars")

    return {
        "draft": draft_text,
        "model": GROQ_MODEL,
        "doc_name": doc_name,
        "prompt_used": prompt
    }