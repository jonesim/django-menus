"""A second admin site for the AdminMenuItem tests: a ModelAdmin with object-level permissions, and a string-pk model."""
from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.urls import path


class LockedUserAdmin(admin.ModelAdmin):
    """Refuses a user named 'locked' to everyone, whatever their model permissions."""

    def has_view_permission(self, request, obj=None):
        return (obj is None or obj.username != 'locked') and super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return (obj is None or obj.username != 'locked') and super().has_change_permission(request, obj)


other_site = admin.AdminSite(name='other_admin')
other_site.register(User, LockedUserAdmin)
other_site.register(Session)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('other-admin/', other_site.urls),
]
