from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from main.forms import EducationForm
from main.models import Education, Experience
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
import datetime

def show_main(request):
    last_login = request.COOKIES.get('last_login', 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "Emil Ananta Kautsar",
        "npm": "2506622121",
        "study_program": "S1 Sistem Informasi",
        "bio": "Mahasiswa fakultas Ilmu Komputer prodi Sistem Informasi Angkatan 2025",
        "last_login": last_login,
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
@login_required(login_url="/login/")
def create_education(request):
    if not request.user.is_superuser:
        raise PermissionDenied


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

# View Mengubah(update) Education
def edit_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    form = EducationForm(request.POST or None, instance=education)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Riwayat pendidikan berhasil diperbarui!")
        return redirect("main:show_education")

    context = {
        "name": "Emil Ananta Kautsar",
        "form": form,
        "education": education,
    }
    return render(request, "education_form.html", context)

# View Menghapus Education
@login_required(login_url="/login/")
def delete_education(request, education_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    
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
    data = serializers.serialize("json", educations, use_natural_foreign_keys=True)
    return HttpResponse(data, content_type="application/json")

def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Emil Ananta Kautsar",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "Emil Ananta Kautsar",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

@login_required(login_url="/login/")
def toggle_star(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST":
        if request.user in education.starred_by.all():
            education.starred_by.remove(request.user)
        else:
            education.starred_by.add(request.user)

    return redirect("main:show_education")
