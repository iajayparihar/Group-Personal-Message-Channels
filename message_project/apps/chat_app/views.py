from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from chat_app.models import Group, GroupMessage, PersonalMessage
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def call(request):
    return render(request,'call.html')

@login_required
def group_chat(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    group_messages = GroupMessage.objects.filter(group=group.pk)
    group_members = group.members.all()

    return render(request, 'group_chat.html', {
        'username': request.user.username,
        'group_name': group.name,
        'group_message': group_messages,
        'group_members': group_members,
    })

@login_required
def personal_chat(request, friend_username):
    friend = get_object_or_404(User, username=friend_username)
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

@login_required
def create_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        members = request.POST.getlist('members')
        group = Group.objects.create(name=group_name, creator=request.user)
        group.members.add(request.user)  # Add the creator to the group
        group.members.add(*members)  # Add selected members to the group
        group.save()
        messages.success(request, 'Group created successfully.')
        return redirect('dashboard')
    
    users = User.objects.exclude(username=request.user.username)
    return render(request, 'create_group.html', {
        'users': users,
    })

@login_required
def manage_group(request, group_name):
    group = get_object_or_404(Group, name=group_name)
    if group.creator != request.user:
        messages.error(request, 'You do not have permission to manage this group.')
        return redirect('dashboard')

    if request.method == 'POST':
        if 'add_member' in request.POST:
            new_member_username = request.POST['new_member']
            new_member = User.objects.get(username=new_member_username)
            group.members.add(new_member)
            messages.success(request, f'{new_member_username} added to the group.')
        elif 'remove_member' in request.POST:
            remove_member_username = request.POST['remove_member']
            remove_member = User.objects.get(username=remove_member_username)
            group.members.remove(remove_member)
            messages.success(request, f'{remove_member_username} removed from the group.')
            
            if remove_member == group.creator:
                remaining_members = group.members.exclude(pk=remove_member.pk)
                if remaining_members.exists():
                    new_creator = remaining_members.first()
                    group.creator = new_creator
                    group.save()
                    messages.success(request, f'{new_creator.username} is now the new group creator.')
                else:
                    group.delete()
                    messages.success(request, 'Group deleted as there are no members left.')
                    return redirect('dashboard')

        elif 'delete_group' in request.POST:
            group.delete()
            messages.success(request, 'Group deleted successfully.')
            return redirect('dashboard')

    group_members = group.members.all()
    users = User.objects.exclude(username=request.user.username).exclude(pk__in=group_members)
    
    return render(request, 'manage_group.html', {
        'group': group,
        'group_members': group_members,
        'users': users,
    })