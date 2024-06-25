from django.contrib import admin

# Register your models here.
from chat_app.models  import Group,GroupMessage,PersonalMessage

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    '''Admin View for Group'''

    list_display = ('name',)

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    '''Admin View for GroupMessage'''

    list_display = ("sender",'content','group',)

@admin.register(PersonalMessage)
class PersonalMessageAdmin(admin.ModelAdmin):
    '''Admin View for PersonalMessage'''

    list_display = ('receiver', 'sender', 'content','seen')