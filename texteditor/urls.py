from django.urls import path

from . import views

urlpatterns = [
    # fmt: off
    path('', views.Home.as_view(), name="home"),
    
    path('notes/create', views.CreateNote.as_view(), name="create_note"),
    path('folders/create', views.CreateFolder.as_view(), name="create_folder"),
    
    path('notes/<str:note_token>/text', views.GetNoteText.as_view(), name="get_note_text"),
    path('notes/<str:note_token>/canvas', views.GetNoteCanvas.as_view(), name="get_note_canvas"),
    path('notes/<int:note_id>/display', views.UpdateDefaultDisplay.as_view(), name="update_default_display"),
    path('notes/<str:note_token>/canvas/save', views.SaveCanvas.as_view(), name="save_note_canvas"),
    path('notes/<int:note_id>/canvas/background', views.UpdateCanvasBackground.as_view(), name="update_canvas_background"),
    
    path('rooms/<int:room_id>/permissions/<str:permission>/update', views.UpdatePermission.as_view(), name="update_permission"),
    path('rooms/<str:note_token>/save', views.SaveRoom.as_view(), name="save_room"),
    
    path('resources/transfer', views.TransferResource.as_view(), name="transfer_resource"),
    path('resources/move', views.MoveResource.as_view(), name="move_resource"),
    
    path('<int:item_id>/<str:item_token>/delete', views.DeleteResource.as_view(), name="delete_resource"),
    path('<int:item_id>/<str:item_token>/rename', views.RenameResource.as_view(), name="rename_resource"),
    
    path('<str:note_token>/r/<str:room_name>', views.TextEditorRoom.as_view(), name="text_editor_room"),
    
    path('<str:folder_token>', views.Home.as_view(), name="home"),
    # fmt: on
]
