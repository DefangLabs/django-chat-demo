from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Moderation fields
    is_flagged = models.BooleanField(default=False)
    moderation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('flagged', 'Flagged for Review'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    moderation_notes = models.JSONField(default=dict)
    moderated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
