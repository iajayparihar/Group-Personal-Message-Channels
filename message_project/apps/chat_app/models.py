from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='chat_groups')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    
    def __str__(self):
        return self.name
    
    class Meta:
        app_label = 'chat_app'

class BaseMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        abstract = True

class GroupMessage(BaseMessage):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    class Meta:
        app_label = 'chat_app'

class PersonalMessage(BaseMessage):
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    class Meta:
        app_label = 'chat_app'

    def __str__(self):
        return f"{self.sender=} : {self.receiver=} "