from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from .models import Company, Opportunity, Workspace


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
    return render(request, "acquisition/settings.html", {"workspace": workspace, "profile": profile})
