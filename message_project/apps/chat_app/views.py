# views.py
from django.shortcuts import render
from django.contrib.auth.models import User
from chat_app.models import Group, GroupMessage, PersonalMessage
from django.db.models import Q

def group_chat(request, group_name):
    group = Group.objects.get(name=group_name)
    group_messages = GroupMessage.objects.filter(group=group.pk)

    return render(request, 'group_chat.html', {
        'username': request.user.username,
        'group_name': group.name,
        'group_message':group_messages,
    })


def personal_chat(request, friend_username):
    friend = User.objects.get(username=friend_username)
    messages = PersonalMessage.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by('timestamp')
    
    return render(request, 'personal_chat.html', {
        'username': request.user.username,
        'friend_username': friend.username,
        'messages' : messages,
    })
