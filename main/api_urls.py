from django.urls import path

from . import api_views

app_name = "api"

urlpatterns = [
    # Education — Tutorial 7
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

    # Experience
    path(
        "experience/",
        api_views.experience_list,
        name="experience-list",
    ),
    path(
        "experience/<uuid:experience_id>/",
        api_views.experience_detail,
        name="experience-detail",
    ),
    path(
        "experience/<uuid:experience_id>/star/",
        api_views.experience_star,
        name="experience-star",
    ),
]