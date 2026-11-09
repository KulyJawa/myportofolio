from django.utils.html import strip_tags
from rest_framework import serializers

from .models import Education, Experience


class EducationSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Education
        fields = [
            "id",
            "institution",
            "degree",
            "start_year",
            "end_year",
            "description",
            "star_count",
            "is_starred",
            "starred_by_names",
        ]
        read_only_fields = ["id"]

    def validate_institution(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError(
                "Nama institusi tidak boleh hanya berisi tag HTML."
            )
        return value

    def validate_degree(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError(
                "Jenjang / jurusan tidak boleh kosong setelah tag HTML dibersihkan."
            )
        return value

    def validate_start_year(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError(
                "Tahun mulai tidak boleh kosong setelah tag HTML dibersihkan."
            )
        return value

    def validate_end_year(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError(
                "Tahun selesai tidak boleh kosong setelah tag HTML dibersihkan."
            )
        return value

    def validate_description(self, value):
        return strip_tags(value or "").strip()

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            return False

        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj):
        return ", ".join(
            user.username for user in obj.starred_by.all()
        )


class ExperienceSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )
    is_ongoing = serializers.BooleanField(read_only=True)

    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = Experience
        fields = [
            "id",
            "title",
            "description",
            "category",
            "category_display",
            "thumbnail",
            "started_at",
            "ended_at",
            "is_ongoing",
            "star_count",
            "is_starred",
            "starred_by_names",
        ]
        read_only_fields = ["id", "started_at"]

    def validate_title(self, value):
        value = strip_tags(value).strip()

        if not value:
            raise serializers.ValidationError(
                "Judul tidak boleh kosong setelah tag HTML dibersihkan."
            )

        return value

    def validate_description(self, value):
        value = strip_tags(value).strip()

        if not value:
            raise serializers.ValidationError(
                "Deskripsi tidak boleh kosong setelah tag HTML dibersihkan."
            )

        return value

    def validate_thumbnail(self, value):
        if not value:
            return value

        # URL gambar hanya boleh memakai HTTP atau HTTPS.
        if not value.lower().startswith(("http://", "https://")):
            raise serializers.ValidationError(
                "URL gambar harus diawali http:// atau https://."
            )

        return value

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            return False

        return request.user in obj.starred_by.all()

    def get_starred_by_names(self, obj):
        return ", ".join(
            user.username for user in obj.starred_by.all()
        )