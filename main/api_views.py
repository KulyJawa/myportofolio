from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Education, Experience
from .permissions import IsPortfolioOwnerOrEditorOrReadOnly
from .serializers import EducationSerializer, ExperienceSerializer


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def education_list(request):
    # Menampilkan daftar education, dengan pencarian opsional.
    if request.method in ("GET", "HEAD"):
        educations = (
            Education.objects
            .prefetch_related("starred_by")
            .order_by("institution", "id")
        )

        institution = request.query_params.get("institution", "").strip()

        if institution:
            educations = educations.filter(
                institution__icontains=institution
            )

        serializer = EducationSerializer(
            educations,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    # Menambahkan education baru.
    serializer = EducationSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def education_detail(request, education_id):
    education = get_object_or_404(
        Education.objects.prefetch_related("starred_by"),
        pk=education_id,
    )

    # Menampilkan satu education.
    if request.method in ("GET", "HEAD"):
        serializer = EducationSerializer(
            education,
            context={"request": request},
        )
        return Response(serializer.data)

    # Menghapus education.
    if request.method == "DELETE":
        education.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Memperbarui education melalui PUT atau PATCH.
    serializer = EducationSerializer(
        education,
        data=request.data,
        partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def education_star(request, education_id):
    education = get_object_or_404(
        Education.objects.prefetch_related("starred_by"),
        pk=education_id,
    )

    # Jika sudah memberi star, batalkan. Jika belum, tambahkan.
    if education.starred_by.filter(pk=request.user.pk).exists():
        education.starred_by.remove(request.user)
    else:
        education.starred_by.add(request.user)

    serializer = EducationSerializer(
        education,
        context={"request": request},
    )
    return Response(serializer.data)


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_list(request):
    if request.method in ("GET", "HEAD"):
        experiences = (
            Experience.objects
            .prefetch_related("starred_by")
            .order_by("-started_at", "id")
        )

        title = request.query_params.get("title", "").strip()

        if title:
            experiences = experiences.filter(title__icontains=title)

        serializer = ExperienceSerializer(
            experiences,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    serializer = ExperienceSerializer(
        data=request.data,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def experience_detail(request, experience_id):
    experience = get_object_or_404(
        Experience.objects.prefetch_related("starred_by"),
        pk=experience_id,
    )

    if request.method in ("GET", "HEAD"):
        serializer = ExperienceSerializer(
            experience,
            context={"request": request},
        )
        return Response(serializer.data)

    if request.method == "DELETE":
        experience.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ExperienceSerializer(
        experience,
        data=request.data,
        partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def experience_star(request, experience_id):
    experience = get_object_or_404(
        Experience.objects.prefetch_related("starred_by"),
        pk=experience_id,
    )

    # Identitas pemberi star selalu berasal dari pengguna yang login.
    if experience.starred_by.filter(pk=request.user.pk).exists():
        experience.starred_by.remove(request.user)
    else:
        experience.starred_by.add(request.user)

    serializer = ExperienceSerializer(
        experience,
        context={"request": request},
    )
    return Response(serializer.data)