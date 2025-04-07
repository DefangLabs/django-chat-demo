from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Room, Message

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'message_count', 'active_users_24h', 'flagged_messages')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'room_statistics')
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Total Messages'
    
    def active_users_24h(self, obj):
        stats = obj.get_statistics()
        return format_html('<span title="Active users in last 24 hours">{} users</span>', 
                         stats['active_users_24h'])
    active_users_24h.short_description = 'Active Users (24h)'
    
    def flagged_messages(self, obj):
        stats = obj.get_statistics()
        if stats['flagged_count'] > 0:
            return format_html(
                '<span style="color: #d9534f;" title="Messages flagged for review">{}</span>',
                stats['flagged_count']
            )
        return '0'
    flagged_messages.short_description = 'Flagged'
    
    def room_statistics(self, obj):
        stats = obj.get_statistics()
        return format_html(
            '<div class="statistics-panel" style="padding: 10px;">' +
            '<h3 style="margin-bottom: 15px;">Room Statistics</h3>' +
            
            '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">' +
            
            # Message Activity Panel
            '<div class="stat-box" style="background: #f8f9fa; padding: 15px; border-radius: 5px;">' +
            '<h4>Message Activity</h4>' +
            '<p>Last 24 hours: <strong>{}</strong></p>' +
            '<p>Last 7 days: <strong>{}</strong></p>' +
            '<p>Total: <strong>{}</strong></p>' +
            '</div>' +
            
            # User Activity Panel
            '<div class="stat-box" style="background: #f8f9fa; padding: 15px; border-radius: 5px;">' +
            '<h4>User Activity</h4>' +
            '<p>Active users (24h): <strong>{}</strong></p>' +
            '<p>Active users (7d): <strong>{}</strong></p>' +
            '</div>' +
            
            # Moderation Panel
            '<div class="stat-box" style="background: #f8f9fa; padding: 15px; border-radius: 5px;">' +
            '<h4>Moderation</h4>' +
            '<p>Flagged messages: <strong style="color: {}">{}</strong></p>' +
            '<p>Pending review: <strong style="color: #f0ad4e">{}</strong></p>' +
            '</div>' +
            
            # Sentiment Panel
            '<div class="stat-box" style="background: #f8f9fa; padding: 15px; border-radius: 5px;">' +
            '<h4>Average Sentiment</h4>' +
            '<p style="color: {}">{}% positive</p>' +
            '</div>' +
            
            '</div>' +
            '</div>',
            
            # Message Activity values
            stats['messages_24h'],
            stats['messages_7d'],
            stats['total_messages'],
            
            # User Activity values
            stats['active_users_24h'],
            stats['active_users_7d'],
            
            # Moderation values
            '#d9534f' if stats['flagged_count'] > 0 else '#6c757d',
            stats['flagged_count'],
            stats['pending_count'],
            
            # Sentiment values
            '#5cb85c' if stats['average_sentiment'] > 0 else '#d9534f' if stats['average_sentiment'] < 0 else '#f0ad4e',
            stats['average_sentiment']
        )
    room_statistics.short_description = 'Room Statistics'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    change_list_template = 'admin/message_changelist.html'
    
    def changelist_view(self, request, extra_context=None):
        # Get base queryset
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        # Add statistics to the context
        response.context_data['flagged_count'] = qs.filter(is_flagged=True).count()
        response.context_data['pending_count'] = qs.filter(moderation_status='pending').count()
        
        # Get today's messages
        today = timezone.now().date()
        response.context_data['today_count'] = qs.filter(created_at__date=today).count()
        
        return response
    list_display = ('truncated_content', 'user', 'room', 'created_at', 'moderation_status_badge', 'moderated_at')
    list_filter = ('moderation_status', 'is_flagged', 'room')
    search_fields = ('content', 'user__username', 'room__name')
    readonly_fields = ('created_at', 'moderated_at', 'sentiment_analysis')
    actions = ['approve_messages', 'flag_messages', 'reject_messages']
    ordering = ('-created_at',)
    
    def truncated_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    truncated_content.short_description = 'Content'
    
    def moderation_status_badge(self, obj):
        colors = {
            'pending': '#f0ad4e',  # Orange
            'approved': '#5cb85c',  # Green
            'flagged': '#d9534f',   # Red
            'rejected': '#292b2c'    # Dark Gray
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.moderation_status, '#6c757d'),
            obj.get_moderation_status_display()
        )
    moderation_status_badge.short_description = 'Status'
    
    def sentiment_analysis(self, obj):
        if not obj.moderation_notes or 'sentiment' not in obj.moderation_notes:
            return 'No sentiment analysis available'
            
        sentiment = obj.moderation_notes['sentiment']
        polarity = sentiment['polarity']
        subjectivity = sentiment['subjectivity']
        
        color = '#5cb85c' if polarity > 0 else '#d9534f' if polarity < 0 else '#f0ad4e'
        
        return format_html(
            '<div style="margin: 10px 0;">' +
            '<div>Sentiment: <span style="color: {}">{}% positive</span></div>' +
            '<div>Subjectivity: {}% subjective</div>' +
            '</div>',
            color,
            round(polarity * 100),
            round(subjectivity * 100)
        )
    sentiment_analysis.short_description = 'Sentiment Analysis'
    
    def approve_messages(self, request, queryset):
        queryset.update(
            moderation_status='approved',
            is_flagged=False,
            moderated_at=timezone.now()
        )
    approve_messages.short_description = 'Approve selected messages'
    
    def flag_messages(self, request, queryset):
        queryset.update(
            moderation_status='flagged',
            is_flagged=True,
            moderated_at=timezone.now()
        )
    flag_messages.short_description = 'Flag selected messages'
    
    def reject_messages(self, request, queryset):
        queryset.update(
            moderation_status='rejected',
            is_flagged=True,
            moderated_at=timezone.now()
        )
    reject_messages.short_description = 'Reject selected messages'
