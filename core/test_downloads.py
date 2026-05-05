import os
import tempfile
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import School, SchoolSetting, SchoolSubscription, SubscriptionPayment, UserProfile


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


class IDCardBulkFormViewTests(SchoolScopedTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='idcard-admin')
        self.client.force_login(self.user)

    def test_bulk_id_card_form_redirects_to_bulk_preview(self):
        response = self.client.post(
            reverse('idcard_bulk_form'),
            {
                'student_class': '8',
                'section': 'A',
            },
        )

        self.assertRedirects(response, f"{reverse('idcard_bulk_preview')}?class=8&section=A")


class DownloadViewTests(SchoolScopedTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username='download-admin')
        self.client.force_login(self.user)

    def test_template_download_returns_excel_attachment(self):
        response = self.client.get(reverse('student_import_template'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('student_import_template.xlsx', response['Content-Disposition'])

    def test_second_download_redirects_to_subscription(self):
        first_response = self.client.get(reverse('student_import_template'))
        second_response = self.client.get(reverse('student_import_template'))

        self.assertEqual(first_response.status_code, 200)
        self.assertRedirects(
            second_response,
            f"{reverse('subscription')}?next=%2Fstudents%2Fimport%2Ftemplate%2F&reason=student-import-template",
            fetch_redirect_response=False,
        )

    def test_database_backup_uses_active_database_path(self):
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as temp_db:
            temp_db.write(b'backup-db')
            temp_db_path = temp_db.name

        self.addCleanup(lambda: os.path.exists(temp_db_path) and os.unlink(temp_db_path))

        with override_settings(
            DATABASES={
                **settings.DATABASES,
                'default': {
                    **settings.DATABASES['default'],
                    'NAME': temp_db_path,
                },
            }
        ):
            response = self.client.get(reverse('database_backup'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('db.sqlite3', response['Content-Disposition'])
        self.assertEqual(b''.join(response.streaming_content), b'backup-db')

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret123')
    @patch('core.views._razorpay_client')
    def test_verified_subscription_payment_unlocks_future_downloads(self, mocked_client_factory):
        first_response = self.client.get(reverse('student_import_template'))
        self.assertEqual(first_response.status_code, 200)

        mocked_client = Mock()
        mocked_client.order.create.return_value = {
            'id': 'order_test_123',
            'amount': 599900,
            'currency': 'INR',
        }
        mocked_client.utility.verify_payment_signature.return_value = None
        mocked_client_factory.return_value = mocked_client

        create_response = self.client.post(reverse('subscription_payment_create'))
        self.assertEqual(create_response.status_code, 200)
        self.assertEqual(create_response.json()['order_id'], 'order_test_123')

        verify_response = self.client.post(
            reverse('subscription_payment_verify'),
            {
                'next': reverse('student_import_template'),
                'razorpay_payment_id': 'pay_test_123',
                'razorpay_order_id': 'order_test_123',
                'razorpay_signature': 'sig_test_123',
            },
        )

        self.assertRedirects(verify_response, reverse('student_import_template'), fetch_redirect_response=False)

        third_response = self.client.get(reverse('student_import_template'))
        self.assertEqual(third_response.status_code, 200)

        subscription = SchoolSubscription.objects.get(school=self.school)
        self.assertIsNotNone(subscription.annual_plan_started_on)
        self.assertIsNotNone(subscription.annual_plan_expires_on)

        payment = SubscriptionPayment.objects.get(order_id='order_test_123')
        self.assertEqual(payment.payment_id, 'pay_test_123')
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_VERIFIED)

    @override_settings(RAZORPAY_KEY_ID='rzp_test_123', RAZORPAY_KEY_SECRET='secret123')
    @patch('core.views._razorpay_client')
    def test_subscription_payment_create_stores_pending_order(self, mocked_client_factory):
        mocked_client = Mock()
        mocked_client.order.create.return_value = {
            'id': 'order_test_pending',
            'amount': 599900,
            'currency': 'INR',
        }
        mocked_client_factory.return_value = mocked_client

        response = self.client.post(reverse('subscription_payment_create'))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['order_id'], 'order_test_pending')
        self.assertTrue(SubscriptionPayment.objects.filter(order_id='order_test_pending').exists())


class SchoolRegistrationViewTests(TestCase):
    def test_register_school_creates_workspace_and_logs_user_in(self):
        response = self.client.post(
            reverse('school_register'),
            {
                'school_name': 'Sunrise Academy',
                'school_address': 'Main Road, City',
                'principal_name': 'Mrs. Khan',
                'username': 'sunrise-admin',
                'admin_email': 'admin@sunrise.test',
                'password1': 'StrongPass123!',
                'password2': 'StrongPass123!',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        school = School.objects.get(name='Sunrise Academy')
        user = get_user_model().objects.get(username='sunrise-admin')
        profile = UserProfile.objects.get(user=user)
        setting = SchoolSetting.objects.get(school=school)

        self.assertEqual(profile.school, school)
        self.assertEqual(setting.school_name, 'Sunrise Academy')
        self.assertEqual(setting.principal_name, 'Mrs. Khan')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)
