from django.contrib import admin
from django.urls import path, include
from .views import login, sign_up, profile

urlpatterns = [
    path('signup/', sign_up),
    path('login/', login),
    path("profile/", profile),
    # path('product/all/', all_products, name='all_products'),
    # path('category/all/', all_categories, name='all_categories'),
    # path("category/add/", add_category, name="add_category"),
    # path('department/all/', all_departments, name='all_departments'),
]