from django.urls import path

from .views import show_main, show_experience, show_education, get_education_json, delete_education, create_education, edit_education, register, login_user, logout_user, toggle_star, create_education_ajax

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("education/", show_education, name="show_education"),
    path("education/add/", create_education, name="create_education"),
    path("education/<uuid:education_id>/delete/", delete_education, name="delete_education"),
    path("api/education/", get_education_json, name="get_education_json"),
    path("education/<uuid:education_id>/edit/", edit_education, name="edit_education"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),    
    path("education/<uuid:education_id>/star/", toggle_star, name="toggle_star"),
    path("education/add-ajax/", create_education_ajax, name="create_education_ajax"),
]