from django.contrib import admin

# Register your models here.
from account.models import Accounts


class AccountsAdmin(admin.ModelAdmin):
    list_display = ("email",)
    list_filter = ("email",)
    search_fields = ("email",)


admin.site.register(Accounts, AccountsAdmin)
