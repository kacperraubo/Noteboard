from django.contrib import admin

# Register your models here.
from texteditor.models import Folder, Note, Room


class RoomAdmin(admin.ModelAdmin):
    list_display = ("user", "name")
    list_filter = ("user",)
    search_fields = ("user",)


class NoteAdmin(admin.ModelAdmin):
    list_display = ("user", "name")
    list_filter = ("user",)
    search_fields = ("user",)


class FolderAdmin(admin.ModelAdmin):
    list_display = ("user", "name")
    list_filter = ("user",)
    search_fields = ("user",)


admin.site.register(Room, RoomAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(Folder, FolderAdmin)
