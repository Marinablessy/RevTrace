"""Strict evidence-grounded proposal generation."""

from openai import OpenAI

from config import (
    GROQ_API_KEY,
    GROQ_BASE_URL,
    GROQ_MODEL,
)


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)


def generate_proposal(
    rfp_text,
    requirements,
    evidence,
    lessons="",
    commercial_context=None,
    account_context=None,
):

    # =====================================================
    # BUILD VERIFIED EVIDENCE
    # =====================================================

    evidence_text = ""

    for item in evidence:

        evidence_text += (
            "\n\n====================================\n"
            f"Requirement ID: {item['requirement_id']}\n"
            f"Requirement: {item['requirement']}\n"
            "Retrieved organizational evidence:\n"
        )

        memories = item.get(
            "memories",
            [],
        )

        if not memories:

            evidence_text += (
                "NO VERIFIED ORGANIZATIONAL EVIDENCE FOUND.\n"
            )

        else:

            for memory in memories:

                evidence_text += (
                    f"- {memory.get('text', '')}\n"
                )


    # =====================================================
    # ACCOUNT CONTEXT
    # =====================================================

    if account_context:

        account_context_text = f"""
Account ID:
{account_context.get('account_id')}

Opportunity ID:
{account_context.get('opportunity_id')}

Company:
{account_context.get('company')}

Industry:
{account_context.get('industry')}

Contact:
{account_context.get('contact_name')}

Role:
{account_context.get('role')}
"""

    else:

        account_context_text = (
            "No RevTrace account context supplied."
        )


    # =====================================================
    # COMMERCIAL CONTEXT
    # =====================================================

    if commercial_context:

        commercial_context_text = f"""
Decision:
{commercial_context.get('decision')}

Originally Requested:
{commercial_context.get('requested_terms')}

APPROVED FINAL TERMS:
{commercial_context.get('final_terms')}

ARR:
{commercial_context.get('arr')}

Segment:
{commercial_context.get('segment')}

Approved By:
{commercial_context.get('approver')}
"""

    else:

        commercial_context_text = (
            "No Deal Desk approved terms supplied."
        )


    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are the Proposal / RFP Agent inside RevTrace.

You must create an enterprise proposal that is STRICTLY
grounded in supplied evidence.

============================================================
MOST IMPORTANT RULE
============================================================

AN RFP REQUIREMENT IS NOT EVIDENCE THAT THE SELLER HAS
THAT CAPABILITY.

If the RFP asks for:

- encryption
- integrations
- dashboards
- analytics
- APIs
- onboarding
- support
- compliance
- access controls
- SLAs
- implementation processes

and there is no explicit organizational evidence proving
that capability, you MUST NOT invent or propose it.

DO NOT write:

"We will provide..."
"We propose..."
"The platform includes..."
"The solution uses..."
"We support..."
"The system integrates..."
"The solution incorporates..."

unless supplied organizational evidence explicitly supports
that exact claim.


============================================================
WHEN EVIDENCE IS MISSING
============================================================

If no verified evidence supports a requirement, write:

"The RFP requires [requirement].
No verified organizational evidence currently confirms
the specific capability or delivery approach.
Human verification required."

Do not design a solution yourself.

Do not create a hypothetical architecture.

Do not invent an implementation approach.

Do not invent assumptions just to complete the proposal.


============================================================
PROHIBITED INVENTIONS
============================================================

Never invent:

- cloud provider integrations
- APIs
- analytics engines
- algorithms
- dashboards
- real-time monitoring
- encryption
- MFA
- RBAC
- audit logging
- certifications
- compliance frameworks
- support hours
- help desks
- escalation paths
- onboarding processes
- implementation phases
- SLAs
- timelines
- customer references
- case studies
- performance metrics
- architecture
- deployment assumptions


============================================================
COMMERCIAL RULES
============================================================

Deal Desk approved terms are authoritative.

Use ONLY:

{commercial_context_text}


If approved terms are:

"25% off annual prepay"

write exactly:

"25% off annual prepay"

Do NOT infer:

- 12-month contract
- annual billing schedule
- renewal period
- contract duration
- payment cadence
- other discounts
- payment terms
- legal terms

Originally requested commercial terms are NOT approved terms.


============================================================
REVTRACE ACCOUNT CONTEXT
============================================================

{account_context_text}


============================================================
HISTORICAL LESSONS
============================================================

{lessons}


============================================================
EXTRACTED RFP REQUIREMENTS
============================================================

{requirements}


============================================================
VERIFIED ORGANIZATIONAL EVIDENCE
============================================================

{evidence_text}


============================================================
ORIGINAL RFP
============================================================

{rfp_text}


============================================================
OUTPUT STRUCTURE
============================================================

Create exactly these sections:

# Executive Summary

Only summarize the customer's stated need and explain that
the response is evidence-grounded.

Do not claim capabilities here unless verified.

# Understanding of Requirements

List the extracted RFP requirements.

For each requirement label it as one of:

- Supported by verified organizational evidence
- Partial evidence
- Human verification required

# Proposed Solution

Only describe capabilities explicitly supported by supplied
organizational evidence.

For unsupported requirements state that the exact solution
approach requires human verification.

Do NOT invent technical designs.

# Technical Approach

Only include verified technical approaches.

If none are verified, say:

"No verified organizational evidence currently confirms
the specific technical implementation approach.
Human verification required."

# Security and Compliance

Only include verified controls and certifications.

If none are verified, explicitly say so.

# Implementation

Only include verified implementation methods.

Never invent phases, timelines or onboarding steps.

# Support and Service

Only include verified support capabilities.

Never invent help desks, support tiers, response times,
on-site support or knowledge bases.

# Relevant Experience

Only include evidence-backed experience.

# Commercial Terms

Use ONLY the exact approved Deal Desk final terms.

# Assumptions and Dependencies

Do NOT invent assumptions.

Only list assumptions explicitly present in the RFP,
organizational evidence or approved commercial context.

Otherwise say:

"No additional verified assumptions or dependencies
have been supplied."

# Items Requiring Confirmation

List every requirement for which verified organizational
evidence is missing.


============================================================
FINAL VALIDATION
============================================================

Before answering, inspect every sentence.

For each vendor capability claim ask:

"Where exactly is the supporting evidence?"

If you cannot point to supplied evidence, remove the claim
and replace it with:

"Human verification required."

Return the proposal only.
"""


    response = client.chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",

                "content": (
                    "You are an extremely conservative "
                    "enterprise proposal writer. "
                    "Never invent capabilities. "
                    "An RFP requirement is not evidence. "
                    "When evidence is absent, explicitly "
                    "require human verification."
                ),
            },

            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0,
    )


    return (
        response
        .choices[0]
        .message.content
    )