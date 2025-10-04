# C:\Users\Vinay\Project\Loopline\community\management\commands\seed_data.py
# FINAL "WORLD BUILDER" VERSION (With All Fixes)

import random
import os
import requests
from io import BytesIO

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress
from community.models import Follow, StatusPost, Group, UserProfile, PostMedia
from faker import Faker
from django.core.files import File
from django.core.files.base import ContentFile

User = get_user_model()

class Command(BaseCommand):
    help = 'Builds a rich world of users with profiles, groups, follows, and posts with media (images & videos).'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='Number of users to create.')
        parser.add_argument('--posts', type=int, default=100, help='Total number of posts to create.')
        parser.add_argument('--groups', type=int, default=10, help='Number of groups to create.')
        parser.add_argument('--max-follows', type=int, default=20, help='Max follows per user.')
        parser.add_argument('--max-groups-joined', type=int, default=5, help='Max groups a user will join.')

    @transaction.atomic
    def handle(self, *args, **options):
        num_users = options['users']
        num_posts = options['posts']
        num_groups = options['groups']
        max_follows = options['max_follows']
        max_groups_joined = options['max_groups_joined']

        self.stdout.write(self.style.SUCCESS('--- Starting Rich World Builder ---'))
        faker = Faker()
        created_users_credentials = []
        users = []
        
        self.stdout.write(f'Creating {num_users} users with profiles...')
        for i in range(num_users):
            first_name = faker.first_name()
            last_name = faker.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(100, 999)}_{i}"
            email = f"{username}@example.com"
            password = "password123"
            try:
                user = User.objects.create_user(
                    username=username, email=email, password=password,
                    first_name=first_name, last_name=last_name
                )
                EmailAddress.objects.update_or_create(
                    user=user, email=user.email,
                    defaults={'primary': True, 'verified': True}
                )
                
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.bio = faker.sentence(nb_words=15)
                
                try:
                    avatar_url = f"https://robohash.org/{username}.png?set=set4"
                    response = requests.get(avatar_url, stream=True, timeout=10)
                    if response.status_code == 200:
                        image_content = ContentFile(response.content)
                        profile.picture.save(f'{username}_avatar.png', image_content, save=True)
                    else:
                        self.stdout.write(self.style.WARNING(f' > Avatar download for {username} failed with status {response.status_code}. Skipping.'))
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.WARNING(f' > Could not fetch avatar for {username} due to network error. Skipping.'))

                users.append(user)
                created_users_credentials.append({'username': username, 'password': password})
            except IntegrityError:
                continue
        self.stdout.write(self.style.SUCCESS(f' > Created {len(users)} users and profiles.'))

        self.stdout.write(f'Creating {num_groups} groups...')
        groups = []
        for i in range(num_groups):
            group_name = faker.company() + " Hub"
            creator = random.choice(users)
            group = Group.objects.create(name=group_name, creator=creator, description=faker.bs(), privacy_level='public' if random.random() < 0.7 else 'private')
            group.members.add(creator) # <-- TYPO FIX APPLIED HERE
            groups.append(group)
        self.stdout.write(self.style.SUCCESS(f' > Created {len(groups)} groups.'))

        self.stdout.write('Populating groups with members...')
        for user in users:
            num_groups_to_join = random.randint(1, min(max_groups_joined, len(groups)))
            groups_to_join = random.sample(groups, num_groups_to_join)
            for group in groups_to_join:
                group.members.add(user)
        self.stdout.write(self.style.SUCCESS(' > Group population complete.'))

        self.stdout.write('Creating the social graph...')
        for user in users:
            num_to_follow = random.randint(1, min(max_follows, len(users) - 1))
            potential_follows = [u for u in users if u != user]
            users_to_follow = random.sample(potential_follows, num_to_follow)
            for user_to_follow in users_to_follow:
                Follow.objects.get_or_create(follower=user, following=user_to_follow)
        self.stdout.write(self.style.SUCCESS(' > Social graph created.'))
        
        self.stdout.write(f'Creating {num_posts} initial posts...')
        seed_media_dir = os.path.join(settings.BASE_DIR.parent, 'seed_media')
        images_dir = os.path.join(seed_media_dir, 'images')
        videos_dir = os.path.join(seed_media_dir, 'videos')

        image_files = [f for f in os.listdir(images_dir) if f.endswith(('jpg', 'jpeg', 'png'))] if os.path.exists(images_dir) else []
        video_files = [f for f in os.listdir(videos_dir) if f.endswith(('mp4', 'mov', 'avi'))] if os.path.exists(videos_dir) else []
        
        for i in range(num_posts):
            author = random.choice(users)
            content = faker.paragraph(nb_sentences=random.randint(2, 5))
            post = StatusPost.objects.create(author=author, content=content)
            roll = random.random()
            if image_files and roll < 0.25:
                image_to_add = random.choice(image_files)
                image_path = os.path.join(images_dir, image_to_add)
                with open(image_path, 'rb') as f:
                    django_file = File(f, name=image_to_add) # <-- FILE OPERATION FIX
                    PostMedia.objects.create(post=post, media_type='image', file=django_file)
            elif video_files and roll < 0.35:
                video_to_add = random.choice(video_files)
                video_path = os.path.join(videos_dir, video_to_add)
                with open(video_path, 'rb') as f:
                    django_file = File(f, name=video_to_add) # <-- FILE OPERATION FIX
                    PostMedia.objects.create(post=post, media_type='video', file=django_file)
        self.stdout.write(self.style.SUCCESS(f' > Created {num_posts} posts.'))
        
        self.stdout.write(self.style.SUCCESS('\n--- MASTER ACCOUNT LOGIN INFO (Sample) ---'))
        for creds in created_users_credentials[:5]:
            self.stdout.write(f"  Username: {creds['username']} | Password: {creds['password']}")
        self.stdout.write(self.style.SUCCESS('-----------------------------------------'))
        self.stdout.write(self.style.WARNING(f'NOTE: Password for ALL {len(users)} seeded users is "password123"'))
        self.stdout.write(self.style.SUCCESS('\n"Rich World Builder" seeding complete!'))