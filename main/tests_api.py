import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Education


class EducationAPITest(APITestCase):
    def setUp(self):
        # Akun percobaan khusus database pengujian.
        self.owner = User.objects.create_superuser(
            username="owner",
            password="test-password",
            email="owner@example.com",
        )
        self.visitor = User.objects.create_user(
            username="visitor",
            password="test-password",
        )

        self.payload = {
            "institution": "Universitas Indonesia",
            "degree": "S1 Sistem Informasi",
            "start_year": "2025",
            "end_year": "Present",
            "description": "Belajar Django REST Framework.",
        }

        self.education = Education.objects.create(**self.payload)

        self.list_url = reverse("api:education-list")
        self.detail_url = reverse(
            "api:education-detail",
            kwargs={"education_id": self.education.pk},
        )
        self.star_url = reverse(
            "api:education-star",
            kwargs={"education_id": self.education.pk},
        )

    # 1. Pengunjung dapat membaca daftar dan detail.
    def test_public_list_and_detail(self):
        self.education.starred_by.add(self.visitor)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

        item = response.data[0]
        self.assertEqual(item["id"], str(self.education.pk))
        self.assertEqual(item["institution"], "Universitas Indonesia")
        self.assertNotIn("fields", item)
        self.assertEqual(item["star_count"], 1)
        self.assertFalse(item["is_starred"])
        self.assertEqual(item["starred_by_names"], "visitor")

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.education.pk))

    # 2. Pencarian tidak membedakan huruf besar/kecil.
    def test_filter_institution(self):
        response = self.client.get(
            self.list_url,
            {"institution": "iNdOnEsIa"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self.client.get(
            self.list_url,
            {"institution": "TidakAdaInstitusiIni"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    # 3. UUID yang tidak ditemukan menghasilkan 404.
    def test_missing_education_returns_404(self):
        url = reverse(
            "api:education-detail",
            kwargs={"education_id": uuid.uuid4()},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    # 4. Guest dan pengguna biasa tidak boleh mengubah pendidikan.
    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            with self.subTest(user=str(user)):
                self.client.force_authenticate(user=user)

                response = self.client.post(
                    self.list_url, self.payload, format="json"
                )
                self.assertEqual(response.status_code, 403)

                response = self.client.patch(
                    self.detail_url,
                    {"institution": "Diubah tanpa izin"},
                    format="json",
                )
                self.assertEqual(response.status_code, 403)

                response = self.client.delete(self.detail_url)
                self.assertEqual(response.status_code, 403)

                self.assertEqual(Education.objects.count(), 1)
                self.education.refresh_from_db()
                self.assertEqual(
                    self.education.institution,
                    "Universitas Indonesia",
                )

    # 5. Superuser boleh membuat data; tag HTML dibersihkan.
    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)

        payload = {
            **self.payload,
            "institution": "<b>Kampus Baru</b>",
            "description": "<p>Deskripsi baru.</p>",
        }
        response = self.client.post(
            self.list_url, payload, format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["institution"], "Kampus Baru")
        self.assertEqual(response.data["description"], "Deskripsi baru.")
        self.assertEqual(Education.objects.count(), 2)

        created = Education.objects.get(pk=response.data["id"])
        self.assertEqual(created.institution, "Kampus Baru")

    # 6. Field wajib kosong atau hanya tag HTML harus ditolak.
    def test_invalid_input_is_rejected(self):
        self.client.force_authenticate(user=self.owner)

        invalid_values = [
            ("institution", ""),
            ("institution", "<b></b>"),
            ("degree", "<b></b>"),
            ("start_year", ""),
            ("end_year", "<b></b>"),
        ]

        for field, value in invalid_values:
            with self.subTest(field=field, value=value):
                payload = {**self.payload, field: value}
                response = self.client.post(
                    self.list_url, payload, format="json"
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
                self.assertIsInstance(response.data[field], list)
                self.assertEqual(Education.objects.count(), 1)

    # 7. PATCH parsial, PUT lengkap, dan DELETE.
    def test_owner_can_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.patch(
            self.detail_url,
            {"institution": "Nama Setelah PATCH"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Nama Setelah PATCH")
        self.assertEqual(self.education.degree, self.payload["degree"])

        # PUT harus menyertakan seluruh field wajib.
        response = self.client.put(
            self.detail_url,
            {"institution": "PUT tidak lengkap"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Nama Setelah PATCH")

        response = self.client.put(
            self.detail_url,
            {**self.payload, "institution": "Nama Setelah PUT"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Nama Setelah PUT")

        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(
            Education.objects.filter(pk=self.education.pk).exists()
        )

    # 8. Star memerlukan login dan dapat dibatalkan.
    def test_star_requires_login_and_toggles(self):
        response = self.client.post(self.star_url, {}, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.education.starred_by.count(), 0)

        self.client.force_authenticate(user=self.visitor)

        response = self.client.post(self.star_url, {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        self.assertTrue(
            self.education.starred_by.filter(pk=self.visitor.pk).exists()
        )

        response = self.client.post(self.star_url, {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)
        self.assertEqual(self.education.starred_by.count(), 0)

    # 9. Pengguna tidak boleh memalsukan field hasil perhitungan.
    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)

        payload = {
            **self.payload,
            "star_count": 99,
            "is_starred": True,
            "starred_by_names": "Nama palsu",
            "starred_by": [self.visitor.pk],
        }
        response = self.client.post(
            self.list_url, payload, format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")

        created = Education.objects.get(pk=response.data["id"])
        self.assertEqual(created.starred_by.count(), 0)

    # 10. Staff saja tidak cukup; Editor boleh edit, bukan tambah/hapus.
    def test_staff_and_editor_permissions(self):
        self.visitor.is_staff = True
        self.visitor.save()
        self.client.force_authenticate(user=self.visitor)

        response = self.client.patch(
            self.detail_url,
            {"institution": "Percobaan staff"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Universitas Indonesia")

        # Sekarang jadikan pengguna Editor, tanpa status staff.
        self.visitor.is_staff = False
        self.visitor.save()
        group, _ = Group.objects.get_or_create(name="Editor")
        self.visitor.groups.add(group)

        response = self.client.patch(
            self.detail_url,
            {"institution": "Diubah Editor"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "Diubah Editor")

        response = self.client.put(
            self.detail_url,
            {**self.payload, "institution": "PUT oleh Editor"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.education.refresh_from_db()
        self.assertEqual(self.education.institution, "PUT oleh Editor")

        response = self.client.post(
            self.list_url, self.payload, format="json"
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), 1)

    # 11. Metode yang tidak didukung menghasilkan 405.
    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(self.list_url)
        self.assertEqual(response.status_code, 405)

        response = self.client.get(self.star_url)
        self.assertEqual(response.status_code, 405)

    # 12. Login melalui session tetap wajib menyertakan CSRF.
    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(
            client.login(username="owner", password="test-password")
        )

        response = client.post(
            self.list_url, self.payload, format="json"
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), 1)

    # 13. Session dengan token CSRF yang valid boleh membuat data.
    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(
            client.login(username="owner", password="test-password")
        )

        # Ambil token asli dari halaman Browsable API.
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, 200)
        self.assertIn("csrftoken", client.cookies)

        token = client.cookies["csrftoken"].value

        response = client.post(
            self.list_url,
            self.payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Education.objects.count(), 2)