from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils.text import slugify
from .models import Room, Message

def index(request):
    rooms = Room.objects.all()
    return render(request, 'chat/index.html', {'rooms': rooms})

@login_required
def create_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            # Create a URL-friendly version of the room name
            room_slug = slugify(room_name)
            room, created = Room.objects.get_or_create(
                name=room_name,
            )
            return redirect('room', room_name=room_slug)
    return redirect('index')

@login_required
def room(request, room_name):
    # Try to find the room by the slugified name
    try:
        room = Room.objects.get(name__iexact=room_name)
    except Room.DoesNotExist:
        # If not found, try to find by the slugified version
        rooms = Room.objects.all()
        room = next((r for r in rooms if slugify(r.name) == room_name), None)
        if not room:
            return redirect('index')
    
    messages = Message.objects.filter(
        room=room
    ).exclude(
        moderation_status__in=['flagged', 'pending']
    ).order_by('created_at')[:50]

    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'chat/register.html', {'form': form})
