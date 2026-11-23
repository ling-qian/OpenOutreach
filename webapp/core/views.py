from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Company, Evidence, Opportunity, ServiceProfile, Workspace


def _workspace_for(user):
    workspace, _ = Workspace.objects.get_or_create(owner=user, defaults={"name": f"{user.username}'s workspace"})
    return workspace


@login_required
def dashboard(request):
    workspace = _workspace_for(request.user)
    context = {
        "workspace": workspace,
        "company_count": Company.objects.filter(workspace=workspace).count(),
        "opportunity_count": Opportunity.objects.filter(workspace=workspace).count(),
        "qualified_count": Opportunity.objects.filter(workspace=workspace, stage="qualified").count(),
        "recent_opportunities": Opportunity.objects.filter(workspace=workspace).select_related("company")[:8],
        "stage_counts": Opportunity.objects.filter(workspace=workspace).values("stage").annotate(total=Count("id")).order_by("stage"),
    }
    return render(request, "acquisition/dashboard.html", context)


@login_required
def leads(request):
    workspace = _workspace_for(request.user)
    companies = Company.objects.filter(workspace=workspace)
    return render(request, "acquisition/leads.html", {"workspace": workspace, "companies": companies})


@login_required
def opportunities(request):
    workspace = _workspace_for(request.user)
    items = Opportunity.objects.filter(workspace=workspace).select_related("company")
    return render(request, "acquisition/opportunities.html", {"workspace": workspace, "opportunities": items})


@login_required
def settings_page(request):
    workspace = _workspace_for(request.user)
    profile = getattr(workspace, "service_profile", None)
    if request.method == "POST":
        profile, _ = ServiceProfile.objects.get_or_create(workspace=workspace)
        profile.service_name = request.POST.get("service_name", "").strip()[:160]
        profile.service_description = request.POST.get("service_description", "").strip()
        profile.ideal_customer_description = request.POST.get("ideal_customer_description", "").strip()
        profile.target_industries = [v.strip() for v in request.POST.get("target_industries", "").split(",") if v.strip()]
        profile.target_locations = [v.strip() for v in request.POST.get("target_locations", "").split(",") if v.strip()]
        profile.save()
        messages.success(request, "Service profile saved.")
        return redirect("settings")
    return render(request, "acquisition/settings.html", {"workspace": workspace, "profile": profile})


@login_required
@require_POST
def discover_companies(request):
    from .discovery import discover
    workspace = _workspace_for(request.user)
    profile = getattr(workspace, "service_profile", None)
    try:
        records = discover(workspace, profile, int(request.POST.get("count", "5")))
        saved = 0
        with transaction.atomic():
            for row in records:
                name = (row.get("company") or "").strip()
                if not name:
                    continue
                domain = (row.get("website") or "").strip()
                website = domain if domain.startswith(("http://", "https://")) else (f"https://{domain}" if domain else "")
                company, created = Company.objects.get_or_create(
                    workspace=workspace, name=name[:240], website=website[:500],
                    defaults={"source": "openoutfind", "icp_verdict": "fit",
                              "icp_reason": row.get("reason", ""),
                              "discovery_source_url": row.get("linkedin_url", "")[:1000],
                              "prospect_contacts": [{
                                  "name": row.get("full_name") or " ".join(filter(None, [row.get("first_name"), row.get("last_name")])),
                                  "title": row.get("title", ""), "profile_url": row.get("linkedin_url", ""),
                                  "email": row.get("email", ""), "reason": row.get("reason", ""),
                              }]})
                if not created:
                    contacts = list(company.prospect_contacts or [])
                    contacts.append({"name": row.get("full_name", ""), "title": row.get("title", ""),
                                     "profile_url": row.get("linkedin_url", ""), "email": row.get("email", ""),
                                     "reason": row.get("reason", "")})
                    company.prospect_contacts = contacts
                    company.save(update_fields=["prospect_contacts", "updated_at"])
                saved += 1
        messages.success(request, f"OpenOutFind returned {len(records)} qualified people; saved {saved} company records.")
    except Exception as exc:
        messages.error(request, f"Discovery failed: {exc}")
    return redirect("leads")


@login_required
@require_POST
def research_company(request, company_id):
    from .research import analyze_page, fetch_page
    workspace = _workspace_for(request.user)
    company = get_object_or_404(Company, pk=company_id, workspace=workspace)
    try:
        if not company.website:
            raise ValueError("Add a website URL to this company before research.")
        page = fetch_page(company.website)
        findings = analyze_page(page)
        with transaction.atomic():
            for item in findings:
                Evidence.objects.create(
                    company=company, category=item["category"], title=item["title"],
                    detail=item["detail"], source_url=page["url"], confidence=item["confidence"])
            opportunity, _ = Opportunity.objects.get_or_create(
                workspace=workspace, company=company,
                defaults={"research_status": "researched"})
            opportunity.research_status = "researched"
            opportunity.save(update_fields=["research_status", "updated_at"])
        messages.success(request, f"Research completed. Captured {len(findings)} evidence-backed signals from {page['url']}.")
    except Exception as exc:
        messages.error(request, f"Website research failed: {exc}")
    return redirect("leads")


@login_required
@require_POST
def generate_opportunity_brief(request, company_id):
    from .briefs import generate_brief
    workspace = _workspace_for(request.user)
    company = get_object_or_404(Company, pk=company_id, workspace=workspace)
    try:
        profile = get_object_or_404(ServiceProfile, workspace=workspace)
        evidence = list(Evidence.objects.filter(company=company).order_by("-observed_at")[:40])
        brief = generate_brief(profile, company, evidence)
        with transaction.atomic():
            opportunity, _ = Opportunity.objects.get_or_create(workspace=workspace, company=company)
            opportunity.score = brief["score"]
            opportunity.summary = brief["summary"]
            opportunity.recommended_service = brief["recommended_service"]
            opportunity.brief_data = brief
            opportunity.research_status = "brief_ready"
            opportunity.save()
        messages.success(request, "Evidence-grounded Opportunity Brief generated and saved.")
    except Exception as exc:
        messages.error(request, f"Brief generation failed: {exc}")
    return redirect("opportunities")
