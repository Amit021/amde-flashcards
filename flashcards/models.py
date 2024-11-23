# flashcards/models.py

from django.db import models
from django.contrib.auth.models import User

class Stack(models.Model):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Word(models.Model):
    german = models.CharField(max_length=255)  # Removed unique=True
    translation = models.CharField(max_length=255)
    sentence = models.TextField(blank=True, null=True)
    sentence_translation = models.TextField(blank=True, null=True)
    stack = models.ForeignKey(Stack, related_name='words', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('german', 'stack')  # Ensures uniqueness within each stack

    def __str__(self):
        return self.german

class UserWordStatus(models.Model):
    STATUS_CHOICES = [
        ('learning', 'Learning'),
        ('reviewing', 'Reviewing'),
        ('mastered', 'Mastered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='learning')
    times_known = models.IntegerField(default=0)
    known_streak = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'word')

    def __str__(self):
        return f"{self.user.username} - {self.word.german} - {self.status}"
