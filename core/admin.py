from django.contrib import admin
from .models import *

class RepositoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
admin.site.register(Repository, RepositoryAdmin)

class RepositoryTypeAdmin(admin.ModelAdmin):
    pass
admin.site.register(RepositoryType, RepositoryTypeAdmin)

class UserAdmin(admin.ModelAdmin):
    pass
admin.site.register(User, UserAdmin)

class UserRoleAdmin(admin.ModelAdmin):
    pass
admin.site.register(UserRole, UserRoleAdmin)

class JoinRequestAdmin(admin.ModelAdmin):
    pass
admin.site.register(JoinRequest, JoinRequestAdmin)

class HarvestProfileAdmin(admin.ModelAdmin):
    pass
admin.site.register(HarvestProfile, HarvestProfileAdmin)

class FindingAidAdmin(admin.ModelAdmin):
    pass
admin.site.register(FindingAid, FindingAidAdmin)

class ControlAccessAdmin(admin.ModelAdmin):
    pass
admin.site.register(ControlAccess, ControlAccessAdmin)

class FindingAidAuditAdmin(admin.ModelAdmin):
    pass
admin.site.register(FindingAidAudit, FindingAidAuditAdmin)

class SubjectHeaderAdmin(admin.ModelAdmin):
    pass
admin.site.register(SubjectHeader, SubjectHeaderAdmin)