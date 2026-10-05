from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from main.forms import EducationForm
from main.models import Education, Experience
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
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

# Render kerangka halaman; kartu diambil dari endpoint JSON melalui JavaScript.
def show_education(request):
    query = request.GET.get("q", "").strip()
    is_editor_user = is_editor(request.user) if request.user.is_authenticated else False
    context = {
        "name": "Emil Ananta Kautsar",
        "query": query,
        "is_editor": is_editor_user,
        "form": EducationForm(),
    }
    return render(request, "education.html", context)

def is_editor(user):
    return user.groups.filter(name='Editor').exists()

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
@login_required(login_url="/login/")
def edit_education(request, education_id):
    if not (request.user.is_superuser or is_editor(request.user)):
        raise PermissionDenied

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
    educations = Education.objects.prefetch_related('starred_by').order_by('institution', 'id')
    
    if query:
        educations = educations.filter(institution__icontains=query)

    data = []
    for edu in educations:
        starred_users = edu.starred_by.all()
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        starred_by_names = ", ".join([u.username for u in starred_users])
        
        data.append({
            "pk": str(edu.id),
            "fields": {
                "institution": edu.institution,
                "degree": edu.degree,
                "start_year": edu.start_year,
                "end_year": edu.end_year,
                "description": edu.description,
                "star_count": starred_users.count(),
                "is_starred": is_starred,
                "starred_by_names": starred_by_names,
            }
        })
    return JsonResponse(data, safe=False)

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

@require_POST
def toggle_star(request, education_id):
    wants_json = "application/json" in request.headers.get("Accept", "")
    if not request.user.is_authenticated:
        if wants_json:
            return JsonResponse({"message": "Silakan login untuk memberi star."}, status=403)
        return redirect("main:login")

    education = get_object_or_404(Education, pk=education_id)

    is_starred = education.starred_by.filter(pk=request.user.pk).exists()
    if is_starred:
        education.starred_by.remove(request.user)
    else:
        education.starred_by.add(request.user)

    if wants_json:
        return JsonResponse({
            "is_starred": not is_starred,
            "star_count": education.starred_by.count(),
            "message": "Star dihapus." if is_starred else "Star ditambahkan.",
        })

    return redirect("main:show_education")

@require_POST
def create_education_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menambahkan riwayat pendidikan."},
            status=403,
        )

    form = EducationForm(request.POST)
    if form.is_valid():
        education = form.save()
        return JsonResponse(
            {"message": "Riwayat pendidikan berhasil ditambahkan.", "pk": str(education.id)},
            status=201,
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
