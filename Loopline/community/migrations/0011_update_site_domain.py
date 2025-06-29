# C:\Users\Vinay\Project\Loopline\community\migrations\0011_update_site_domain.py

from django.db import migrations
from django.conf import settings

# --- The name and domain for the production site ---
# We get the domain from the NETLIFY_APP_URL environment variable if it exists.
# We strip "https://", "http://", and trailing slashes for a clean domain.
APP_DOMAIN = "nxtturn.netlify.app" # Hardcoding for simplicity and reliability
APP_NAME = "NxtTurn"

def update_site_domain(apps, schema_editor):
    """
    Finds the default Site object and updates its domain and name
    to match our live application's settings.
    """
    Site = apps.get_model('sites', 'Site')
    
    # We are updating the site with pk=1, as defined in settings.py
    try:
        default_site = Site.objects.get(pk=settings.SITE_ID)
        
        print(f"Updating site ID {settings.SITE_ID}...")
        print(f"  - Old domain: {default_site.domain}")
        print(f"  - Old name: {default_site.name}")

        default_site.domain = APP_DOMAIN
        default_site.name = APP_NAME
        default_site.save()

        print(f"  + New domain: {default_site.domain}")
        print(f"  + New name: {default_site.name}")

    except Site.DoesNotExist:
        # This will only run if a site with pk=1 doesn't exist, which is unlikely.
        print(f"Site with ID {settings.SITE_ID} not found, creating a new one.")
        Site.objects.create(
            pk=settings.SITE_ID,
            domain=APP_DOMAIN,
            name=APP_NAME,
        )


class Migration(migrations.Migration):

    dependencies = [
        # This migration depends on the one before it.
        ('community', '0010_alter_postmedia_file_alter_userprofile_picture'),
        # It also depends on the sites framework being set up.
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        # This is the command that runs our function.
        migrations.RunPython(update_site_domain),
    ]