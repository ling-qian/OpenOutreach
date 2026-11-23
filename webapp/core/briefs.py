"""Evidence-grounded opportunity brief generation using OpenOutFind's LLM factory."""
from __future__ import annotations

import json


def generate_brief(profile, company, evidence):
    from pydantic import BaseModel, Field
    from pydantic_ai import Agent
    from openoutfind.core.llm import get_llm_model, run_agent_sync

    class Finding(BaseModel):
        evidence_ids: list[int] = Field(description="Only IDs supplied in the evidence list")
        problem: str
        business_impact: str
        recommended_action: str
        service_fit: str
        priority: int = Field(ge=1, le=5)

    class Brief(BaseModel):
        summary: str
        recommended_service: str
        findings: list[Finding]
        score: int = Field(ge=0, le=100)

    evidence_payload = [{
        "id": item.pk, "category": item.category, "title": item.title,
        "detail": item.detail, "source_url": item.source_url,
    } for item in evidence]
    if not evidence_payload:
        raise ValueError("No website evidence exists. Research the company before generating a brief.")
    prompt = (
        "Create a concise B2B opportunity brief. Use only the supplied evidence. "
        "Do not claim a problem unless at least one supplied evidence ID supports it. "
        "Every finding must cite one or more supplied evidence IDs. If evidence is weak, "
        "say so in the wording and lower priority. Do not infer traffic, rankings, revenue, "
        "or competitor performance. Return at most 6 findings.\n\n"
        + json.dumps({
            "service_profile": {
                "service": profile.service_name,
                "description": profile.service_description,
                "ideal_customer": profile.ideal_customer_description,
            },
            "company": {"name": company.name, "website": company.website, "industry": company.industry, "location": company.location},
            "evidence": evidence_payload,
        }, ensure_ascii=False)
    )
    agent = Agent(get_llm_model(), output_type=Brief, system_prompt="You are a cautious B2B website research analyst. Never invent evidence.")
    result = run_agent_sync(agent.run(prompt))
    return result.output.model_dump()
