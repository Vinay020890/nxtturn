# In 0012_create_superuser.py
import os
from django.db import migrations

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if username and email and password and not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)

class Migration(migrations.Migration):
    dependencies = [('community', '0011_update_site_domain')]
    operations = [migrations.RunPython(create_superuser)]