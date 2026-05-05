import shutil
import tempfile
from datetime import date
from zipfile import ZipFile
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from .forms import StudentForm
from .models import FeeReceipt, School, Student, UserProfile
from .views import _require_school


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
    b"\x00\x04\x00\x01\xf61\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


class SchoolScopedTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.school = School.objects.create(name='Test School', address='Test Address')

    def create_user(self, **kwargs):
        user_model = get_user_model()
        defaults = {
            'username': 'admin',
            'password': 'pass1234',
        }
        defaults.update(kwargs)
        user = user_model.objects.create_user(**defaults)
        UserProfile.objects.create(user=user, school=self.school)
        return user


class SchoolMiddlewareTests(SchoolScopedTestCase):
    def test_home_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, reverse('login'))

    def test_dashboard_uses_school_from_user_profile(self):
        user = self.create_user(username='middleware-admin')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_to_school_register_when_user_has_no_school(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username='no-school-dashboard', password='pass1234')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(response, reverse('school_register'))

    def test_require_school_recovers_from_user_profile_when_request_school_missing(self):
        user = self.create_user(username='request-school-admin')
        request = HttpRequest()
        request.user = user
        request.school = None

        school = _require_school(request)

        self.assertEqual(school, self.school)
        self.assertEqual(request.school, self.school)

    def test_require_school_raises_when_user_has_no_school_profile(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username='no-school', password='pass1234')
        request = HttpRequest()
        request.user = user
        request.school = None

        with self.assertRaises(PermissionDenied):
            _require_school(request)

    def test_dashboard_shows_fee_summary_for_selected_year_for_current_school(self):
        user = self.create_user(username='fee-dashboard-admin')
        self.client.force_login(user)
        student = Student.objects.create(
            school=self.school,
            name='Aarav Sharma',
            father_name='Rakesh Sharma',
            dob='2012-06-15',
            student_class='8',
            section='A',
            roll_no='12',
            admission_no='ADM-2026-001',
            address='123 Main Road',
            mobile='9876543210',
        )
        FeeReceipt.objects.create(
            school=self.school,
            student=student,
            receipt_no='FEE-2026-001',
            receipt_date=date(2026, 4, 1),
            tuition_fee=1000,
            library_fee=100,
            paid_amount=700,
        )
        FeeReceipt.objects.create(
            school=self.school,
            student=student,
            receipt_no='FEE-2026-002',
            receipt_date=date(2026, 5, 1),
            tuition_fee=500,
            donation=50,
            paid_amount=550,
        )
        FeeReceipt.objects.create(
            school=self.school,
            student=student,
            receipt_no='FEE-2025-001',
            receipt_date=date(2025, 5, 1),
            tuition_fee=300,
            paid_amount=100,
        )

        other_school = School.objects.create(name='Other School', address='Other Address')
        other_student = Student.objects.create(
            school=other_school,
            name='Other Student',
            father_name='Other Father',
            dob='2012-06-15',
            student_class='8',
            section='A',
            roll_no='13',
            admission_no='ADM-OTHER-001',
            address='456 Main Road',
            mobile='9876543211',
        )
        FeeReceipt.objects.create(
            school=other_school,
            student=other_student,
            receipt_no='FEE-2026-001',
            receipt_date=date(2026, 4, 1),
            tuition_fee=9999,
            paid_amount=9999,
        )

        response = self.client.get(reverse('dashboard'), {'fee_year': 2026})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['fee_years'], [2026, 2025])
        self.assertEqual(response.context['selected_fee_year'], 2026)
        self.assertEqual(response.context['selected_fee_summary']['total_fees'], 1650)
        self.assertEqual(response.context['selected_fee_summary']['collected_fees'], 1250)
        self.assertEqual(response.context['selected_fee_summary']['remaining_fees'], 400)
        self.assertContains(response, 'Total Fees Collected')
        self.assertContains(response, '&#8377;1650')

        response = self.client.get(reverse('dashboard'), {'fee_year': 2025})

        self.assertEqual(response.context['selected_fee_year'], 2025)
        self.assertEqual(response.context['selected_fee_summary']['total_fees'], 300)
        self.assertEqual(response.context['selected_fee_summary']['collected_fees'], 100)
        self.assertEqual(response.context['selected_fee_summary']['remaining_fees'], 200)


class IDCardGenerationTests(SchoolScopedTestCase):
    def setUp(self):
        super().setUp()
        self.temp_media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.temp_media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(lambda: shutil.rmtree(self.temp_media_root, ignore_errors=True))

        self.user = self.create_user()
        self.client.force_login(self.user)

    def test_id_card_html_uses_root_media_url_for_student_photo(self):
        student = Student.objects.create(
            school=self.school,
            name='Aarav Sharma',
            father_name='Rakesh Sharma',
            dob='2012-06-15',
            student_class='8',
            section='A',
            roll_no='12',
            admission_no='ADM-2026-001',
            address='123 Main Road',
            mobile='9876543210',
            photo=SimpleUploadedFile('student.png', PNG_BYTES, content_type='image/png'),
        )

        response = self.client.get(reverse('idcard_html', kwargs={'student_id': student.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aarav Sharma')
        self.assertContains(response, '/media/students/photos/student.png')

    def test_id_card_jpg_download_returns_jpeg(self):
        student = Student.objects.create(
            school=self.school,
            name='Aarav Sharma',
            father_name='Rakesh Sharma',
            dob='2012-06-15',
            student_class='8',
            section='A',
            roll_no='12',
            admission_no='ADM-2026-010',
            address='123 Main Road',
            mobile='9876543210',
            photo=SimpleUploadedFile('student.png', PNG_BYTES, content_type='image/png'),
        )

        response = self.client.get(reverse('idcard_jpg', kwargs={'student_id': student.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertIn('id-card-ADM-2026-010.jpg', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'\xff\xd8'))

    def test_second_id_card_download_redirects_to_subscription(self):
        student = Student.objects.create(
            school=self.school,
            name='Aarav Sharma',
            father_name='Rakesh Sharma',
            dob='2012-06-15',
            student_class='8',
            section='A',
            roll_no='12',
            admission_no='ADM-2026-019',
            address='123 Main Road',
            mobile='9876543210',
        )

        first_response = self.client.get(reverse('idcard_jpg', kwargs={'student_id': student.id}))
        second_response = self.client.get(reverse('idcard_jpg', kwargs={'student_id': student.id}))

        self.assertEqual(first_response.status_code, 200)
        self.assertRedirects(
            second_response,
            f"{reverse('subscription')}?next=%2Fdocuments%2Fid-card%2F{student.id}%2Fjpg%2F&reason=id-card-jpg",
            fetch_redirect_response=False,
        )

    def test_bulk_id_card_jpg_download_returns_zip(self):
        Student.objects.create(
            school=self.school,
            name='Aarav Sharma',
            father_name='Rakesh Sharma',
            dob='2012-06-15',
            student_class='8',
            section='A',
            roll_no='12',
            admission_no='ADM-2026-011',
            address='123 Main Road',
            mobile='9876543210',
        )
        Student.objects.create(
            school=self.school,
            name='Vihaan Khan',
            father_name='Salman Khan',
            dob='2012-07-20',
            student_class='8',
            section='A',
            roll_no='13',
            admission_no='ADM-2026-012',
            address='456 Park Lane',
            mobile='9876500000',
        )

        response = self.client.get(reverse('idcard_bulk_jpg'), {'class': '8', 'section': 'A'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('id-cards-class-8-section-A.zip', response['Content-Disposition'])

        archive = ZipFile(BytesIO(response.content))
        self.assertEqual(
            sorted(archive.namelist()),
            ['id-card-ADM-2026-011.jpg', 'id-card-ADM-2026-012.jpg'],
        )


class StudentFormTransliterationTests(SchoolScopedTestCase):
    @patch('core.views.translate_text', return_value='अरफात')
    def test_translation_endpoint_returns_marathi_text(self, mocked_translate):
        user = self.create_user(username='admin3')
        self.client.force_login(user)

        response = self.client.post(
            reverse('student_transliterate'),
            data='{"text":"arfat"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('text', payload)
        self.assertEqual(payload['text'], 'अरफात')
        mocked_translate.assert_called_once_with('arfat', fail_silently=False)

    @patch('core.views.translate_text', return_value='यासर')
    def test_translation_endpoint_accepts_legacy_get_requests(self, mocked_translate):
        user = self.create_user(username='admin5')
        self.client.force_login(user)

        response = self.client.get(reverse('student_transliterate'), {'text': 'yaser'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['text'], 'यासर')
        mocked_translate.assert_called_once_with('yaser', fail_silently=False)

    @patch('core.forms.translate_text', side_effect=lambda value: f'mr:{value}')
    def test_translation_endpoint_requires_csrf(self, mocked_translate):
        user = self.create_user(username='admin4')
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(
            reverse('student_transliterate'),
            data='{"text":"arfat"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        mocked_translate.assert_not_called()


class StudentBulkImportTests(SchoolScopedTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='import-admin')
        self.client.force_login(self.user)

    def _build_excel_upload(self, headers, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(headers)
        for row in rows:
            sheet.append(row)

        content = BytesIO()
        workbook.save(content)
        content.seek(0)
        return SimpleUploadedFile(
            'students.xlsx',
            content.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    @patch('core.forms.translate_text', side_effect=lambda value: f'mr:{value}')
    def test_bulk_import_accepts_documented_short_format(self, mocked_translate):
        upload = self._build_excel_upload(
            [
                'name',
                'father_name',
                'dob',
                'gender',
                'student_class',
                'section',
                'roll_no',
                'admission_no',
                'address',
                'mobile',
                'status',
            ],
            [
                [
                    'Aarav Sharma',
                    'Rakesh Sharma',
                    '2012-06-15',
                    'male',
                    '8',
                    'A',
                    '12',
                    'ADM-2026-101',
                    '123 Main Road, City',
                    '9876543210',
                    'active',
                ]
            ],
        )

        response = self.client.post(reverse('student_bulk_import'), {'excel_file': upload})

        self.assertRedirects(response, reverse('student_list'))
        student = Student.objects.get(school=self.school, admission_no='ADM-2026-101')
        self.assertEqual(student.name, 'Aarav Sharma')
        self.assertEqual(student.father_name, 'Rakesh Sharma')
        self.assertEqual(student.gender, 'male')
        self.assertEqual(student.address, '123 Main Road, City')
        self.assertEqual(student.status, 'active')
        self.assertEqual(mocked_translate.call_count, 3)

    @patch('core.forms.translate_text', side_effect=lambda value: f'mr:{value}')
    def test_bulk_import_accepts_day_month_year_dob_strings(self, mocked_translate):
        upload = self._build_excel_upload(
            [
                'name',
                'father_name',
                'dob',
                'gender',
                'student_class',
                'section',
                'roll_no',
                'admission_no',
                'address',
                'mobile',
                'status',
            ],
            [
                [
                    'Aarav Sharma',
                    'Rakesh Sharma',
                    '15/06/2012',
                    'male',
                    '8',
                    'A',
                    '13',
                    'ADM-2026-103',
                    '123 Main Road, City',
                    '9876543210',
                    'active',
                ]
            ],
        )

        response = self.client.post(reverse('student_bulk_import'), {'excel_file': upload})

        self.assertRedirects(response, reverse('student_list'))
        student = Student.objects.get(school=self.school, admission_no='ADM-2026-103')
        self.assertEqual(student.dob.isoformat(), '2012-06-15')
        self.assertEqual(student.gender, 'male')
        self.assertEqual(mocked_translate.call_count, 3)

    def test_bulk_import_rejects_unknown_header_format(self):
        upload = self._build_excel_upload(
            ['name', 'dob', 'admission_no'],
            [['Aarav Sharma', '2012-06-15', 'ADM-2026-102']],
        )

        response = self.client.post(reverse('student_bulk_import'), {'excel_file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid format. Please download and use the provided template.')
        self.assertFalse(Student.objects.filter(school=self.school, admission_no='ADM-2026-102').exists())

    @patch('core.forms.translate_text', side_effect=lambda value: f'mr:{value}')
    def test_english_marathi_fields_are_translated_on_save(self, mocked_translate):
        form = StudentForm(
            school=self.school,
            data={
                'name': 'yaser arfat',
                'name_mr': 'yaser arfat',
                'father_name': 'yusuf hussain',
                'father_name_mr': 'yusuf hussain',
                'mother_name': 'khadeer unisa',
                'mother_name_mr': 'khadeer unisa',
                'religion': 'muslim',
                'religion_mr': 'muslim',
                'caste': 'open',
                'caste_mr': 'open',
                'mother_tongue': 'urdu',
                'mother_tongue_mr': 'urdu',
                'father_occupation': 'electricition',
                'father_occupation_mr': 'electricition',
                'dob': '2000-12-13',
                'gender': 'male',
                'birth_place': 'Nanded',
                'birth_place_mr': 'Nanded',
                'taluka': 'Nanded',
                'taluka_mr': 'Nanded',
                'district': 'Nanded',
                'district_mr': 'Nanded',
                'student_class': '1',
                'section': 'A',
                'roll_no': '1',
                'admission_no': 'ADM-TEST-001',
                'register_page_no': '',
                'previous_school_name': 'sana school nanded',
                'previous_school_name_mr': 'sana school nanded',
                'previous_school_class': '',
                'address': 'hyder bagh no 1',
                'address_mr': 'hyder bagh no 1',
                'mobile': '9657575187',
                'status': 'active',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        student = form.save()

        self.assertEqual(student.name_mr, 'mr:yaser arfat')
        self.assertEqual(student.father_name_mr, 'mr:yusuf hussain')
        self.assertEqual(student.gender, 'male')
        self.assertEqual(student.address_mr, 'mr:hyder bagh no 1')
        self.assertEqual(mocked_translate.call_count, 12)

    @patch('core.forms.translate_text', side_effect=lambda value: f'mr:{value}')
    def test_student_add_view_translates_marathi_fields_before_save(self, mocked_translate):
        user = self.create_user(username='admin2')
        self.client.force_login(user)

        response = self.client.post(
            reverse('student_add'),
            data={
                'name': 'muheet',
                'name_mr': 'muheet',
                'father_name': 'mazher',
                'father_name_mr': 'mazher',
                'mother_name': 'mahida',
                'mother_name_mr': 'mahida',
                'religion': 'muslim',
                'religion_mr': 'muslim',
                'caste': 'muslim',
                'caste_mr': 'muslim',
                'mother_tongue': 'hindi',
                'mother_tongue_mr': 'hindi',
                'father_occupation': 'doctor',
                'father_occupation_mr': 'doctor',
                'dob': '2008-01-01',
                'gender': 'male',
                'birth_place': 'nanded',
                'birth_place_mr': 'nanded',
                'taluka': 'nanded',
                'taluka_mr': 'nanded',
                'district': 'nanded',
                'district_mr': 'nanded',
                'student_class': '1',
                'section': 'A',
                'roll_no': '33',
                'admission_no': 'ADM-VIEW-001',
                'register_page_no': '',
                'previous_school_name': 'sana school',
                'previous_school_name_mr': 'sana school',
                'previous_school_class': '',
                'address': 'hyder bagh',
                'address_mr': 'hyder bagh',
                'mobile': '9999999999',
                'status': 'active',
            },
        )

        self.assertEqual(response.status_code, 302)
        student = Student.objects.get(school=self.school, admission_no='ADM-VIEW-001')
        self.assertEqual(student.name_mr, 'mr:muheet')
        self.assertEqual(student.father_name_mr, 'mr:mazher')
        self.assertEqual(student.gender, 'male')
        self.assertEqual(student.address_mr, 'mr:hyder bagh')
        self.assertEqual(mocked_translate.call_count, 12)

    @patch('core.forms.translate_text', side_effect=lambda value: f'mr:{value}')
    def test_manual_marathi_text_is_not_overwritten_on_save(self, mocked_translate):
        form = StudentForm(
            school=self.school,
            data={
                'name': 'yaser arfat',
                'name_mr': 'यासर अरफात',
                'father_name': 'yusuf hussain',
                'father_name_mr': 'युसूफ हुसेन',
                'mother_name': 'khadeer unisa',
                'mother_name_mr': 'खदीर उनिसा',
                'religion': 'muslim',
                'religion_mr': 'मुस्लिम',
                'caste': 'open',
                'caste_mr': 'ओपन',
                'mother_tongue': 'urdu',
                'mother_tongue_mr': 'उर्दू',
                'father_occupation': 'electricition',
                'father_occupation_mr': 'इलेक्ट्रीशियन',
                'dob': '2000-12-13',
                'gender': 'male',
                'birth_place': 'Nanded',
                'birth_place_mr': 'नांदेड',
                'taluka': 'Nanded',
                'taluka_mr': 'नांदेड',
                'district': 'Nanded',
                'district_mr': 'नांदेड',
                'student_class': '1',
                'section': 'A',
                'roll_no': '1',
                'admission_no': 'ADM-TEST-002',
                'register_page_no': '',
                'previous_school_name': 'sana school nanded',
                'previous_school_name_mr': 'सना स्कूल नांदेड',
                'previous_school_class': '',
                'address': 'hyder bagh no 1',
                'address_mr': 'हैदर बाग नं 1',
                'mobile': '9657575187',
                'status': 'active',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        student = form.save()

        self.assertEqual(student.name_mr, 'यासर अरफात')
        self.assertEqual(student.address_mr, 'हैदर बाग नं 1')
        mocked_translate.assert_not_called()
