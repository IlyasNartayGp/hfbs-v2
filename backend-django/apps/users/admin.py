from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "created_at"]
    search_fields = ["name", "email"]
    readonly_fields = ["id", "created_at"]
