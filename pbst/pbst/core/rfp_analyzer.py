"""RFP analysis functionality."""
import json

from openai import OpenAI

from config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL
)


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL
)


def analyze_rfp(rfp_text):

    prompt = f"""
You are an RFP requirement analysis agent.

Analyze the RFP below and extract ONLY explicit
customer requirements.

Do not invent requirements.

For every requirement return:

- id
- requirement
- priority
- category
- evidence_quote

Allowed priority values:

High
Medium
Low

Allowed categories:

Technical
Functional
Security
Compliance
Support
Implementation
Integration
Performance
Deliverables
Commercial
Timeline
Evaluation

Return ONLY valid JSON.

Required format:

{{
  "requirements": [
    {{
      "id": "R1",
      "requirement": "...",
      "priority": "High",
      "category": "Technical",
      "evidence_quote": "..."
    }}
  ]
}}

RFP:

{rfp_text}
"""


    response = client.chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You extract explicit RFP requirements "
                    "without inventing information."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )


    content = response.choices[0].message.content

    result = json.loads(content)

    return result["requirements"]