from django.urls import path

from . import api_views

app_name = "api"

urlpatterns = [
    path(
        "education/",
        api_views.education_list,
        name="education-list",
    ),
    path(
        "education/<uuid:education_id>/",
        api_views.education_detail,
        name="education-detail",
    ),
    path(
        "education/<uuid:education_id>/star/",
        api_views.education_star,
        name="education-star",
    ),
]