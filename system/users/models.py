from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class College(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        FACULTY = 'FACULTY', 'Faculty'
        CLIENT = 'CLIENT', 'Client'
        UESO = 'UESO', 'UESO'
        COORDINATOR = 'COORDINATOR', 'College Coordinator'
        DEAN = 'DEAN', 'College Dean'
        PROGRAM_HEAD = 'PROGRAM_HEAD', 'Program Head'
        DIRECTOR = 'DIRECTOR', 'Director of Extension'
        VP = 'VP', 'Vice President'

    class Sex(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'

    class Campus(models.TextChoices):
        MAIN = 'MAIN', 'Main'
        RIZAL = 'RIZAL', 'Rizal'
        NARRA = 'NARRA', 'Narra'
        QUEZON = 'QUEZON', 'Quezon'
        ARACELI = 'ARACELI', 'Araceli'
        BROOKES_POINT = 'BROOKES_POINT', "Brooke's Point"
        SAN_VICENTE = 'SAN_VICENTE', 'San Vicente'
        CUYO = 'CUYO', 'Cuyo'
        CORON = 'CORON', 'Coron'
        BALABAC = 'BALABAC', 'Balabac'
        ROXAS = 'ROXAS', 'Roxas'
        TAYTAY = 'TAYTAY', 'Taytay'
        EL_NIDO = 'EL_NIDO', 'El Nido'
        LINAPACAN = 'LINAPACAN', 'Linapacan'
        SAN_RAFAEL = 'SAN_RAFAEL', 'San Rafael'
        SOFRONIO_ESPANOLA = 'SOFRONIO_ESPANOLA', 'Sofronio Española'
        DUMARAN = 'DUMARAN', 'Dumaran'
        BATARAZA = 'BATARAZA', 'Bataraza'

    # User fields
    given_name = models.CharField(max_length=150)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    last_name = models.CharField(max_length=150)
    suffix = models.CharField(max_length=10, blank=True, null=True)
    sex = models.CharField(max_length=6, choices=Sex.choices)
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=20)
    campus = models.CharField(max_length=30, choices=Campus.choices)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.PUBLIC)
    degree = models.CharField(max_length=255, blank=True, null=True)
    expertise = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=255, blank=True, null=True)
    is_expert = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    created_at = models.DateTimeField(auto_now_add=True)

    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'given_name', 'last_name', 'sex', 'contact_no', 'campus', 'role']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_full_name(self):
        mi = f"{self.middle_initial}. " if self.middle_initial else ""
        suffix = f" {self.suffix}" if self.suffix else ""
        return f"{self.given_name} {mi}{self.last_name}{suffix}"