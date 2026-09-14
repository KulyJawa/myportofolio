from django.shortcuts import render

from main.models import Experience, Education


def show_main(request):
    context = {
        "name": "Emil",
        "npm": "2506622121",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Mahasiswa fakultas Ilmu Komputer prodi Sistem Informasi Angkatan 2025 "
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Emil",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

# Tambahan education
def show_education(request):
    context = {
        "name": "Emil Ananta Kautsar",
        "education_list": Education.objects.all(),
    }
    return render(request, "education.html", context)