from django.db import models
from django.contrib.auth.models import User

from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

class Room(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def get_statistics(self):
        """Get room statistics including message counts and sentiment averages"""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Base queryset for messages in this room
        messages = self.messages.all()
        
        # Message counts
        total_messages = messages.count()
        messages_24h = messages.filter(created_at__gte=last_24h).count()
        messages_7d = messages.filter(created_at__gte=last_7d).count()
        
        # Moderation stats
        flagged_count = messages.filter(is_flagged=True).count()
        pending_count = messages.filter(moderation_status='pending').count()
        
        # Active users
        active_users_24h = messages.filter(
            created_at__gte=last_24h
        ).values('user').distinct().count()
        
        active_users_7d = messages.filter(
            created_at__gte=last_7d
        ).values('user').distinct().count()
        
        # Average sentiment (excluding messages without sentiment)
        sentiment_avg = messages.exclude(
            Q(moderation_notes={}) | 
            ~Q(moderation_notes__has_key='sentiment')
        ).annotate(
            sentiment=Avg('moderation_notes__sentiment__polarity')
        ).aggregate(avg_sentiment=Avg('sentiment'))['avg_sentiment'] or 0
        
        return {
            'total_messages': total_messages,
            'messages_24h': messages_24h,
            'messages_7d': messages_7d,
            'flagged_count': flagged_count,
            'pending_count': pending_count,
            'active_users_24h': active_users_24h,
            'active_users_7d': active_users_7d,
            'average_sentiment': round(sentiment_avg * 100, 1)  # as percentage
        }

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
