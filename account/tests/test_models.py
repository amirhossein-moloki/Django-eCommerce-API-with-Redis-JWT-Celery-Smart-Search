from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from account.models import Profile, Address

User = get_user_model()


class UserModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+989123456789',
            username='testuser',
            password='password123',
            first_name='Test',
            last_name='User'
        )

    def test_create_user(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.phone_number, '+989123456789')
        self.assertTrue(self.user.check_password('password123'))

    def test_create_user_without_phone_number(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(phone_number=None, password='password123')

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='superuser@example.com',
            username='superuser',
            password='password123',
            phone_number='+989123456788',
            first_name='Super',
            last_name='User'
        )
        self.assertEqual(User.objects.count(), 2)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_active)

    def test_create_superuser_without_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                phone_number='+989123456787',
                password='password123',
                is_staff=False
            )

    def test_create_superuser_without_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                phone_number='+989123456786',
                password='password123',
                is_superuser=False
            )

    def test_user_str_representation(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_user_name_property(self):
        self.assertEqual(self.user.name, 'Test User')

    def test_username_validator(self):
        user = User(username='invalid username', email='test@test.com')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_phone_number_validator(self):
        user = User(phone_number='123', email='test@test.com', username='testuser')
        with self.assertRaises(ValidationError):
            user.full_clean()


class ProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+989123456785',
            username='testuser',
            password='password123'
        )

    def test_profile_creation_signal(self):
        # The signal should have created a profile automatically
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        self.assertEqual(self.user.profile.balance, 0.0)

    def test_profile_str_representation(self):
        self.assertEqual(str(self.user.profile), f'Profile of {self.user}')


class AddressModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+989123456784',
            username='testuser',
            password='password123'
        )
        self.address = Address.objects.create(
            user=self.user,
            province='Tehran',
            city='Tehran',
            postal_code='1234567890',
            full_address='Main Street',
            receiver_name='Test User',
            receiver_phone='+989123456789'
        )

    def test_create_address(self):
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(self.address.user, self.user)

    def test_address_str_representation(self):
        expected_str = 'Main Street, Tehran, Tehran'
        self.assertEqual(str(self.address), expected_str)
