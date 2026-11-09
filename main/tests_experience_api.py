import re
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Experience


User = get_user_model()


class ExperienceAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "test-password-123"

        cls.owner = User.objects.create_superuser(
            username="experience_owner",
            email="owner@example.com",
            password=cls.password,
        )

        cls.visitor = User.objects.create_user(
            username="experience_visitor",
            password=cls.password,
        )

        cls.editor = User.objects.create_user(
            username="experience_editor",
            password=cls.password,
        )

        editor_group, _ = Group.objects.get_or_create(name="Editor")
        cls.editor.groups.add(editor_group)

        # Status staff saja tidak boleh memberikan izin edit.
        cls.staff = User.objects.create_user(
            username="experience_staff",
            password=cls.password,
            is_staff=True,
        )

        cls.experience = Experience.objects.create(
            title="Magang Backend Developer",
            description="Membuat API Django.",
            category="internship",
        )

    def setUp(self):
        self.list_url = reverse("api:experience-list")

        self.detail_url = reverse(
            "api:experience-detail",
            kwargs={"experience_id": self.experience.pk},
        )

        self.star_url = reverse(
            "api:experience-star",
            kwargs={"experience_id": self.experience.pk},
        )

        self.payload = {
            "title": "Asisten Dosen",
            "description": "Membantu kegiatan praktikum.",
            "category": "part-time",
            "thumbnail": "",
            "ended_at": None,
        }

    def database_snapshot(self):
        """Catat data dan relasi star untuk memeriksa perubahan."""
        records = list(
            Experience.objects.order_by("pk").values()
        )

        stars = [
            (
                str(item.pk),
                list(
                    item.starred_by.order_by("pk")
                    .values_list("pk", flat=True)
                ),
            )
            for item in Experience.objects.order_by("pk")
        ]

        return records, stars

    # 1. Semua peran boleh membaca daftar dan detail.
    def test_all_roles_can_read(self):
        expected_fields = {
            "id", "title", "description", "category",
            "category_display", "thumbnail",
            "started_at", "ended_at", "is_ongoing",
            "star_count", "is_starred", "starred_by_names",
        }

        for user in (
            None, self.visitor, self.editor, self.owner
        ):
            with self.subTest(user=str(user)):
                self.client.force_authenticate(user=user)

                response = self.client.get(self.list_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.data), 1)

                response = self.client.get(self.detail_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    set(response.data.keys()),
                    expected_fields,
                )
                self.assertEqual(response.data["star_count"], 0)
                self.assertFalse(response.data["is_starred"])

    # 2. Pencarian berdasarkan judul.
    def test_search_by_title(self):
        Experience.objects.create(
            title="Relawan Perpustakaan",
            description="Membantu pengelolaan buku.",
            category="volunteer",
        )

        response = self.client.get(
            self.list_url, {"title": "mAgAnG"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            str(self.experience.pk),
        )

        response = self.client.get(
            self.list_url, {"title": "zzzzzz"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        response = self.client.get(
            self.list_url, {"title": ""}
        )
        self.assertEqual(len(response.data), 2)

    # 3. ID yang tidak ditemukan menghasilkan 404.
        # 3. ID yang tidak ditemukan menghasilkan 404.
    def test_missing_experience_returns_404(self):
        missing_id = uuid.uuid4()

        detail_url = reverse(
            "api:experience-detail",
            kwargs={"experience_id": missing_id},
        )
        star_url = reverse(
            "api:experience-star",
            kwargs={"experience_id": missing_id},
        )

        self.client.force_authenticate(user=self.owner)

        # GET tidak membutuhkan payload.
        before = self.database_snapshot()

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.database_snapshot(), before)

        # PUT/PATCH mengirim data JSON; DELETE tidak perlu body.
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                before = self.database_snapshot()

                if method == "delete":
                    response = self.client.delete(detail_url)
                else:
                    response = getattr(self.client, method)(
                        detail_url,
                        self.payload,
                        format="json",
                    )

                self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    self.database_snapshot(), before
                )

        before = self.database_snapshot()

        response = self.client.post(
            star_url, {}, format="json"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.database_snapshot(), before)

    # 4. Tamu, pengguna biasa, dan staff tanpa Editor ditolak.
    def test_non_editors_cannot_modify_experiences(self):
        operations = [
            ("post", self.list_url),
            ("put", self.detail_url),
            ("patch", self.detail_url),
            ("delete", self.detail_url),
        ]

        for user in (None, self.visitor, self.staff):
            self.client.force_authenticate(user=user)

            for method, url in operations:
                with self.subTest(user=str(user), method=method):
                    before = self.database_snapshot()

                    response = getattr(self.client, method)(
                        url,
                        self.payload,
                        format="json",
                    )

                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(
                        self.database_snapshot(), before
                    )

    # 5. Editor boleh PUT/PATCH, tetapi tidak POST/DELETE.
    def test_editor_permissions(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.patch(
            self.detail_url,
            {"title": "Judul dari Editor"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.experience.refresh_from_db()
        self.assertEqual(
            self.experience.title, "Judul dari Editor"
        )
        self.assertEqual(
            self.experience.description, "Membuat API Django."
        )

        response = self.client.put(
            self.detail_url,
            self.payload,
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.experience.refresh_from_db()
        self.assertEqual(
            self.experience.description,
            self.payload["description"],
        )

        for method, url in (
            ("post", self.list_url),
            ("delete", self.detail_url),
        ):
            with self.subTest(method=method):
                before = self.database_snapshot()

                response = getattr(self.client, method)(
                    url, self.payload, format="json"
                )

                self.assertEqual(response.status_code, 403)
                self.assertEqual(
                    self.database_snapshot(), before
                )

    # 6. Superuser bisa tambah, edit, dan hapus.
    def test_superuser_crud(self):
        self.client.force_authenticate(user=self.owner)

        payload = {
            **self.payload,
            "title": "<b>Asisten Dosen</b>",
            "description": "<p>Membantu praktikum.</p>",
        }

        response = self.client.post(
            self.list_url, payload, format="json"
        )
        self.assertEqual(response.status_code, 201)

        created = Experience.objects.get(pk=response.data["id"])
        self.assertEqual(created.title, "Asisten Dosen")
        self.assertEqual(created.description, "Membantu praktikum.")

        detail_url = reverse(
            "api:experience-detail",
            kwargs={"experience_id": created.pk},
        )

        response = self.client.patch(
            detail_url,
            {"title": "Judul diperbarui"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        created.refresh_from_db()
        self.assertEqual(created.title, "Judul diperbarui")
        self.assertEqual(created.description, "Membantu praktikum.")

        response = self.client.put(
            detail_url, self.payload, format="json"
        )
        self.assertEqual(response.status_code, 200)

        created.refresh_from_db()
        self.assertEqual(created.title, self.payload["title"])

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(
            Experience.objects.filter(pk=created.pk).exists()
        )

    # 7. Input tidak valid ditolak tanpa membuat data.
    def test_invalid_create_does_not_change_database(self):
        self.client.force_authenticate(user=self.owner)

        invalid_values = [
            ("title", ""),
            ("title", "<b></b>"),
            ("title", "x" * 256),
            ("description", ""),
            ("description", "<p></p>"),
            ("category", "kategori-tidak-ada"),
            ("thumbnail", "bukan-url"),
            ("thumbnail", "ftp://example.com/image.png"),
            ("ended_at", "bukan-tanggal"),
        ]

        for field, value in invalid_values:
            with self.subTest(field=field, value=value):
                before = self.database_snapshot()
                payload = {**self.payload, field: value}

                response = self.client.post(
                    self.list_url, payload, format="json"
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
                self.assertEqual(
                    self.database_snapshot(), before
                )

    # 8. PATCH invalid dan PUT tidak lengkap tidak mengubah data.
    def test_invalid_updates_do_not_change_database(self):
        self.client.force_authenticate(user=self.owner)

        cases = [
            ("patch", {"title": "<b></b>"}, "title"),
            ("put", {"title": "Hanya judul"}, "description"),
        ]

        for method, payload, field in cases:
            with self.subTest(method=method):
                before = self.database_snapshot()

                response = getattr(self.client, method)(
                    self.detail_url, payload, format="json"
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
                self.assertEqual(
                    self.database_snapshot(), before
                )

    # 9. Tamu tidak boleh memberi star.
    def test_guest_cannot_star(self):
        before = self.database_snapshot()

        response = self.client.post(
            self.star_url, {}, format="json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.database_snapshot(), before)

    # 10. Pengguna login dapat star/unstar atas nama dirinya.
    def test_authenticated_roles_can_toggle_own_star(self):
        for user in (self.visitor, self.editor, self.owner):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)

                # ID pengguna lain di payload harus diabaikan.
                response = self.client.post(
                    self.star_url,
                    {"user_id": self.staff.pk},
                    format="json",
                )

                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.data["is_starred"])
                self.assertEqual(response.data["star_count"], 1)
                self.assertEqual(
                    response.data["starred_by_names"],
                    user.username,
                )
                self.assertEqual(
                    list(
                        self.experience.starred_by.values_list(
                            "pk", flat=True
                        )
                    ),
                    [user.pk],
                )

                # Status harus tetap benar pada GET berikutnya.
                response = self.client.get(self.detail_url)
                self.assertTrue(response.data["is_starred"])

                response = self.client.post(
                    self.star_url, {}, format="json"
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.data["is_starred"])
                self.assertEqual(response.data["star_count"], 0)
                self.assertEqual(
                    self.experience.starred_by.count(), 0
                )

    # 11. Field readonly dan relasi star tidak bisa dipalsukan.
    def test_readonly_fields_cannot_be_overwritten(self):
        self.client.force_authenticate(user=self.owner)

        original_id = self.experience.pk
        original_started_at = self.experience.started_at

        response = self.client.patch(
            self.detail_url,
            {
                "title": "Judul sah",
                "id": str(uuid.uuid4()),
                "started_at": "2000-01-01T00:00:00Z",
                "is_ongoing": False,
                "star_count": 999,
                "is_starred": True,
                "starred_by_names": "palsu",
                "starred_by": [self.visitor.pk],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.experience.refresh_from_db()
        self.assertEqual(self.experience.pk, original_id)
        self.assertEqual(
            self.experience.started_at, original_started_at
        )
        self.assertEqual(self.experience.title, "Judul sah")
        self.assertTrue(response.data["is_ongoing"])
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertEqual(self.experience.starred_by.count(), 0)

    # 12. Metode HTTP yang tidak didukung menghasilkan 405.
    def test_wrong_methods_are_rejected(self):
        self.client.force_authenticate(user=self.owner)
        before = self.database_snapshot()

        response = self.client.delete(self.list_url)
        self.assertEqual(response.status_code, 405)

        response = self.client.get(self.star_url)
        self.assertEqual(response.status_code, 405)

        self.assertEqual(self.database_snapshot(), before)

    # 13. Session login tetap memerlukan CSRF untuk perubahan data.
    def test_session_authentication_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)

        logged_in = client.login(
            username=self.owner.username,
            password=self.password,
        )
        self.assertTrue(logged_in)

        # Ambil token dari form pada halaman Experience.
        page = client.get(reverse("main:show_experience"))
        self.assertEqual(page.status_code, 200)

        token_match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            page.content.decode(),
        )
        self.assertIsNotNone(token_match)
        token = token_match.group(1)

        operations = [
            ("post", self.list_url),
            ("put", self.detail_url),
            ("patch", self.detail_url),
            ("delete", self.detail_url),
            ("post", self.star_url),
        ]

        # Session valid, tetapi tanpa header token: tetap ditolak.
        for method, url in operations:
            with self.subTest(method=method, url=url):
                before = self.database_snapshot()

                response = getattr(client, method)(
                    url, self.payload, format="json"
                )

                self.assertEqual(response.status_code, 403)
                self.assertEqual(
                    self.database_snapshot(), before
                )

        # Dengan token yang valid: penambahan berhasil.
        response = client.post(
            self.list_url,
            self.payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Experience.objects.count(), 2)