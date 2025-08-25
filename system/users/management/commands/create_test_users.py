from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Create one test user for each role"

    def handle(self, *args, **kwargs):
        roles = [choice[0] for choice in User.Role.choices]
        default_password = "test1234"
 
        for role in roles:
            email = f"{role.lower()}@example.com"
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=role.lower(),
                    email=email,
                    password=default_password,
                    given_name=role.capitalize(),
                    middle_initial="T",
                    last_name="User",
                    sex=User.Sex.MALE,
                    contact_no="0999999999",
                    campus=User.Campus.MAIN,
                    role=role,
                )
                self.stdout.write(self.style.SUCCESS(f"Created {role} user: {email} / {default_password}"))
            else:
                self.stdout.write(self.style.WARNING(f"{role} user already exists."))
