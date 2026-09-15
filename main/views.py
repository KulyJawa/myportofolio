from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from main.forms import EducationForm
from main.models import Education, Experience

def show_main(request):
    context = {
        "name": "Emil Ananta Kautsar",
        "npm": "2506622121",
        "study_program": "S1 Sistem Informasi",
        "bio": "Mahasiswa fakultas Ilmu Komputer prodi Sistem Informasi Angkatan 2025",
    }
    return render(request, "index.html", context)

def show_experience(request):
    context = {
        "name": "Emil Ananta Kautsar",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

# View Halaman Education dengan Filter & Deserialisasi
def show_education(request):
    json_response = get_education_json(request)
    edu_objects = serializers.deserialize("json", json_response.content.decode("utf-8"))
    education_list = [item.object for item in edu_objects]

    query = request.GET.get("q", "").strip()
    context = {
        "name": "Emil Ananta Kautsar",
        "education_list": education_list,
        "query": query,
    }
    return render(request, "education.html", context)

# View Menambah Education
def create_education(request):
    form = EducationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Riwayat pendidikan berhasil ditambahkan!")
        return redirect("main:show_education")

    context = {
        "name": "Emil Ananta Kautsar",
        "form": form,
    }
    return render(request, "education_form.html", context)

# View Menghapus Education
def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    if request.method == "POST":
        education.delete()
        messages.success(request, "Riwayat pendidikan berhasil dihapus!")
    return redirect("main:show_education")

# Endpoint Data Delivery JSON
def get_education_json(request):
    query = request.GET.get("q", "").strip()
    educations = Education.objects.all()
    if query:
        educations = educations.filter(institution__icontains=query)
    data = serializers.serialize("json", educations)
    return HttpResponse(data, content_type="application/json")