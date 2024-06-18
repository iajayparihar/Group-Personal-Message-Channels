from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/group/(?P<group_name>\w+)/$', consumers.GroupChatConsumer.as_asgi()),
    re_path(r'ws/personal/(?P<friend_username>[\w.@+-]+)/$', consumers.PersonalChatConsumer.as_asgi()),
    re_path(r'ws/call/', consumers.CallConsumer.as_asgi()),
]
