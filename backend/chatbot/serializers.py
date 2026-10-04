from rest_framework import serializers

from .models import ChatMessage


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)


class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()
    message_id = serializers.IntegerField(required=False)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "sender", "content", "created_at")
        read_only_fields = fields
