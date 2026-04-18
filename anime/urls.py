from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.anime_search, name='anime_search'),
    path('view/<int:anime_id>/', views.anime_view, name='anime_view'),
    path('random/', views.random_anime, name='random_anime'),
    path('list/', views.view_list, name='view_list'),
    path('add/<int:anime_id>/', views.add_to_list, name="add_to_list"),
    path('delete/<int:anime_id>/', views.deactivate_anime, name="remove_from_list"),
    path('increment/<int:anime_id>/', views.quick_progress_increment, name="quick_increment"),
     path('search_list/', views.list_search, name='list_search')
]
