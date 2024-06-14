from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from chat_app.models import Group, GroupMessage, PersonalMessage
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def group_chat(request, group_name):
    group = Group.objects.get(name=group_name)
    group_messages = GroupMessage.objects.filter(group=group.pk)

    return render(request, 'group_chat.html', {
        'username': request.user.username,
        'group_name': group.name,
        'group_message': group_messages,
    })

@login_required
def personal_chat(request, friend_username):
    friend = User.objects.get(username=friend_username)
    messages = PersonalMessage.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by('timestamp')
    
    return render(request, 'personal_chat.html', {
        'username': request.user.username,
        'friend_username': friend.username,
        'messages': messages,
    })

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('user_login')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return redirect('user_register')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('user_register')
        user = User.objects.create_user(username=username, password=password)
        user.save()
        messages.success(request, 'Registration successful. Please log in.')
        return redirect('user_login')
    return render(request, 'register.html')

@login_required
def dashboard(request):
    user_groups = request.user.chat_groups.all()
    users = User.objects.exclude(username=request.user.username)
    
    return render(request, 'dashboard.html', {
        'username': request.user.username,
        'groups': user_groups,
        'users': users,
    })
