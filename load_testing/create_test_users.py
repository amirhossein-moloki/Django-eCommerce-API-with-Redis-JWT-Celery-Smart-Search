import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_api.settings')
django.setup()

User = get_user_model()

def create_test_users(count=100):
    """Creates a specified number of test users."""
    for i in range(count):
        phone_number = f'555555{i:04d}'
        password = 'testpassword'
        if not User.objects.filter(phone_number=phone_number).exists():
            User.objects.create_user(
                phone_number=phone_number,
                password=password,
                is_active=True,
                is_profile_complete=True
            )
    print(f'{count} test users created successfully.')

if __name__ == '__main__':
    create_test_users()
