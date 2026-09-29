from groq import Groq

from backend.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
)


groq_client = Groq(
    api_key=GROQ_API_KEY
)


def generate_outreach_message(
    name: str,
    company: str,
    industry: str,
    role: str,
    company_size: str,
    pain_point: str,
    recommended_angle: str,
    memories: list[dict],
):
    memory_text = "\n".join(
        f"- {memory['representative_memory']}"
        for memory in memories[:5]
    )

    prompt = f"""
You are an AI outbound sales assistant.

Write a short personalized cold outreach email.

PROSPECT DETAILS
Name: {name}
Company: {company}
Industry: {industry}
Role: {role}
Company size: {company_size}
Pain point: {pain_point}

RECOMMENDED STRATEGY
Message angle: {recommended_angle}

RELEVANT HISTORICAL MEMORIES
{memory_text}

RULES
- Use the recommended messaging angle only as a strategy.
- Personalize only with facts explicitly provided in PROSPECT DETAILS.
- Historical memories are INTERNAL EVIDENCE only.
- Never turn historical memories into claims about our company,
  our customers, our experience, or the market.
- Never say phrases such as:
  "we have helped similar companies",
  "many companies face this",
  "this is a common challenge",
  "companies like yours",
  or similar unsupported claims.
- Never invent company growth, market position, statistics,
  percentages, savings, case studies, customers, product features,
  capabilities, results, or achievements.
- Do not infer anything about the prospect that was not supplied.
- If a fact is unknown, omit it.
- Focus directly on the stated pain point.
- Keep the email under 120 words.
- Include a short subject line.
- Use a natural professional tone.
- Include a low-pressure call to action.
- Return only the final email.
- Do not describe what "I", "we", or "our team" has done unless that
  information is explicitly provided.
- Do not claim experience working with similar companies or industries.
- Prefer neutral wording such as "A cost-efficiency discussion may help..."
  instead of inventing seller experience.
"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
    "role": "system",
    "content": (
        "You are a strictly grounded B2B outreach writer. "
        "Never invent facts. Historical examples may guide strategy "
        "but must never be presented as customer claims or market facts."
    ),
},
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content