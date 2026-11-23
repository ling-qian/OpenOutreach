from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from .models import Company, Opportunity


def _workspace_for(user):
    return user.acquisition_workspaces.order_by("id").first()


@login_required
def dashboard(request):
    workspace = _workspace_for(request.user)
    if not workspace:
        return render(request, "acquisition/empty_workspace.html")
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
    companies = Company.objects.filter(workspace=workspace) if workspace else Company.objects.none()
    return render(request, "acquisition/leads.html", {"workspace": workspace, "companies": companies})


@login_required
def opportunities(request):
    workspace = _workspace_for(request.user)
    items = Opportunity.objects.filter(workspace=workspace).select_related("company") if workspace else Opportunity.objects.none()
    return render(request, "acquisition/opportunities.html", {"workspace": workspace, "opportunities": items})


@login_required
def settings_page(request):
    workspace = _workspace_for(request.user)
    profile = getattr(workspace, "service_profile", None) if workspace else None
    return render(request, "acquisition/settings.html", {"workspace": workspace, "profile": profile})
