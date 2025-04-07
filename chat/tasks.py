from celery import shared_task
from django.utils import timezone
from textblob import TextBlob
from better_profanity import profanity
import nltk
from .models import Room, Message

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

@shared_task
def moderate_message_content(message_id):
    """
    Analyze message content for harmful language or harassment
    """
    try:
        message = Message.objects.get(id=message_id)
        content = message.content
        moderation_notes = {}

        # Check for profanity
        if profanity.contains_profanity(content):
            moderation_notes['profanity'] = True
            message.is_flagged = True

        # Sentiment analysis using TextBlob
        blob = TextBlob(content)
        sentiment = blob.sentiment
        moderation_notes['sentiment'] = {
            'polarity': sentiment.polarity,  # -1 to 1 (negative to positive)
            'subjectivity': sentiment.subjectivity  # 0 to 1 (objective to subjective)
        }

        # Flag negative content (more sensitive for kids)
        if sentiment.polarity < -0.35 and sentiment.subjectivity > 0.5:
            moderation_notes['negative_content'] = True
            message.is_flagged = True
            moderation_notes['flag_reason'] = 'Potentially negative or unfriendly message'

        # Update message status
        if message.is_flagged:
            message.moderation_status = 'flagged'
            moderation_notes['flagged_at'] = timezone.now().isoformat()
        else:
            message.moderation_status = 'approved'

        message.moderation_notes = moderation_notes
        message.moderated_at = timezone.now()
        message.save()

        return {
            'message_id': message_id,
            'is_flagged': message.is_flagged,
            'status': message.moderation_status,
            'notes': moderation_notes
        }

    except Message.DoesNotExist:
        return f"Message with id {message_id} not found"

@shared_task
def clean_old_messages(days=7):
    """
    Delete messages older than the specified number of days
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    deleted_count = Message.objects.filter(created_at__lt=cutoff_date).delete()[0]
    return f"Deleted {deleted_count} old messages"

@shared_task
def count_room_messages(room_id):
    """
    Count the number of messages in a room
    """
    try:
        room = Room.objects.get(id=room_id)
        message_count = room.messages.count()
        return f"Room '{room.name}' has {message_count} messages"
    except Room.DoesNotExist:
        return f"Room with id {room_id} not found"
