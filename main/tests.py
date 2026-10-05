from django.test import Client, TestCase
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Education


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )
        self.education = Education.objects.create(
            institution="Universitas Indonesia",
            degree="S1 Sistem Informasi",
            start_year="2025",
            end_year="Present",
            description="Fakultas Ilmu Komputer",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')
        self.assertContains(response, f'href="{reverse("main:show_education")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")

    def test_education_url_is_accessible(self):
        response = self.client.get(reverse("main:show_education"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education.html")

    def test_education_page_displays_data(self):
        response = self.client.get(reverse("main:show_education"))
        # Halaman hanya berisi kerangka; data diambil melalui endpoint AJAX.
        self.assertNotContains(response, f"<h2>{self.education.institution}</h2>")
        self.assertContains(response, 'id="grid"')
        data = self.client.get(reverse("main:get_education_json")).json()
        self.assertEqual(data[0]["fields"]["institution"], self.education.institution)

    def test_empty_education_page(self):
        Education.objects.all().delete()
        response = self.client.get(reverse("main:show_education"))
        self.assertContains(response, 'id="empty"')
        self.assertEqual(self.client.get(reverse("main:get_education_json")).json(), [])

class EducationAjaxTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser('owner', password='test-only-password')
        cls.editor = User.objects.create_user('editor', password='test-only-password')
        cls.editor.groups.add(Group.objects.create(name='Editor'))
        cls.reader = User.objects.create_user('reader', password='test-only-password')
        cls.payload = {
            'institution': 'Universitas Indonesia', 'degree': 'S1 Sistem Informasi',
            'start_year': '2025', 'end_year': 'Present', 'description': '',
        }
        cls.education = Education.objects.create(**cls.payload)

    def test_page_and_public_json_for_all_roles(self):
        self.education.starred_by.add(self.reader)
        for user in [None, self.reader, self.editor, self.owner]:
            with self.subTest(user=user):
                self.client.logout()
                if user:
                    self.client.force_login(user)
                page = self.client.get(reverse('main:show_education'))
                self.assertEqual(page.status_code, 200)
                self.assertNotContains(page, f"<h2>{self.education.institution}</h2>")
                if user == self.owner:
                    self.assertContains(page, 'id="education-form"')
                else:
                    self.assertNotContains(page, 'id="education-form"')
                data = self.client.get(reverse('main:get_education_json')).json()[0]['fields']
                self.assertEqual(data['star_count'], 1)
                self.assertEqual(data['is_starred'], user == self.reader)

    def test_search_and_empty_result(self):
        endpoint = reverse('main:get_education_json')
        self.assertEqual(len(self.client.get(endpoint, {'q': 'INDONESIA'}).json()), 1)
        self.assertEqual(self.client.get(endpoint, {'q': 'tidak ditemukan'}).json(), [])

    def test_create_only_for_owner(self):
        endpoint = reverse('main:create_education_ajax')
        for user in [None, self.reader, self.editor]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            response = self.client.post(endpoint, self.payload)
            self.assertEqual(response.status_code, 403)
            self.assertIn('message', response.json())
        self.assertEqual(Education.objects.count(), 1)
        self.client.force_login(self.owner)
        response = self.client.post(endpoint, self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Education.objects.filter(pk=response.json()['pk']).exists())
        self.assertEqual(self.client.get(endpoint).status_code, 405)

    def test_invalid_and_html_only_fields_are_rejected(self):
        self.client.force_login(self.owner)
        endpoint = reverse('main:create_education_ajax')
        response = self.client.post(endpoint, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn('institution', response.json()['errors'])
        for field in ['institution', 'degree', 'start_year', 'end_year']:
            response = self.client.post(endpoint, {**self.payload, field: '<b>'})
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.json()['errors'])

    def test_xss_payload_is_removed_and_optional_description_is_allowed(self):
        self.client.force_login(self.owner)
        endpoint = reverse('main:create_education_ajax')
        response = self.client.post(endpoint, {
            **self.payload, 'institution': '<b>UI</b>',
            'description': '<img src="x" onerror="alert(\'XSS!\')">',
        })
        self.assertEqual(response.status_code, 201)
        education = Education.objects.get(pk=response.json()['pk'])
        self.assertEqual(education.institution, 'UI')
        self.assertEqual(education.description, '')
        response = self.client.post(endpoint, self.payload)
        self.assertEqual(response.status_code, 201)

    def test_csrf_is_required_for_create_and_star(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        create_url = reverse('main:create_education_ajax')
        star_url = reverse('main:toggle_star', args=[self.education.pk])
        self.assertEqual(client.post(create_url, self.payload).status_code, 403)
        self.assertEqual(client.post(star_url).status_code, 403)
        client.get(reverse('main:show_education'))
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(create_url, self.payload, HTTP_X_CSRFTOKEN=token).status_code, 201)
        self.assertEqual(client.post(star_url, HTTP_X_CSRFTOKEN=token,
                                     HTTP_ACCEPT='application/json').status_code, 200)

    def test_star_permissions_and_toggle(self):
        endpoint = reverse('main:toggle_star', args=[self.education.pk])
        self.assertEqual(self.client.post(endpoint, HTTP_ACCEPT='application/json').status_code, 403)
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(endpoint).status_code, 405)
        response = self.client.post(endpoint, HTTP_ACCEPT='application/json')
        self.assertEqual(response.json()['star_count'], 1)
        self.assertTrue(response.json()['is_starred'])
        response = self.client.post(endpoint, HTTP_ACCEPT='application/json')
        self.assertEqual(response.json()['star_count'], 0)
        self.assertFalse(response.json()['is_starred'])

    def test_existing_edit_and_delete_permissions(self):
        edit_url = reverse('main:edit_education', args=[self.education.pk])
        delete_url = reverse('main:delete_education', args=[self.education.pk])
        self.client.force_login(self.reader)
        self.assertEqual(self.client.post(edit_url, self.payload).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(edit_url, self.payload).status_code, 302)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertFalse(Education.objects.filter(pk=self.education.pk).exists())
