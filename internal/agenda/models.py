from django.db import models
from system.users.models import College

class Agenda(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField()
	concerned_colleges = models.ManyToManyField(College, related_name='agendas')

	def __str__(self):
		return self.name
