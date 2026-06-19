from django.urls import path # type: ignore
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipe/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipe/new/', views.recipe_create, name='recipe_create'),
    path('recipe/<int:recipe_pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipe/<int:recipe_pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('recipe/<int:recipe_pk>/session/new/', views.session_create, name='session_create'),
    path('session/<int:pk>/', views.session_detail, name='session_detail'),
    path('session/<int:pk>/edit/', views.session_edit, name='session_edit'),
    path('session/<int:pk>/delete/', views.session_delete, name='session_delete'),
]