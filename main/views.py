from django.shortcuts import render

from main.models import Experience


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