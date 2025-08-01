# Generated by Django 5.2 on 2025-07-05 14:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0014_merge_0012_update_site_domain_0013_create_superuser'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('reason', models.CharField(choices=[('SPAM', 'Spam or Misleading'), ('HARASSMENT', 'Harassment or Bullying'), ('HATE_SPEECH', 'Hate Speech'), ('VIOLENCE', 'Violence or Graphic Content'), ('OTHER', 'Other')], max_length=20)),
                ('details', models.TextField(blank=True, help_text="Provide more details if 'Other' is selected.", null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Review'), ('REVIEWED', 'Under Review'), ('ACTION_TAKEN', 'Action Taken'), ('DISMISSED', 'Dismissed')], default='PENDING', max_length=20)),
                ('moderated_at', models.DateTimeField(blank=True, null=True)),
                ('moderator_notes', models.TextField(blank=True, help_text='Notes for internal review.', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('moderator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='moderated_reports', to=settings.AUTH_USER_MODEL)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submitted_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('reporter', 'content_type', 'object_id')},
            },
        ),
    ]
