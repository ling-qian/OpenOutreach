from django.contrib import admin
from .models import Company, Evidence, Opportunity, OutreachDraft, ServiceProfile, Workspace

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name", "owner__username", "owner__email")

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "industry", "location", "workspace")
    search_fields = ("name", "website", "industry")

admin.site.register(ServiceProfile)
admin.site.register(Evidence)
admin.site.register(Opportunity)
admin.site.register(OutreachDraft)
