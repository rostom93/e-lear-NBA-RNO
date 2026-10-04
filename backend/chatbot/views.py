from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage
from .serializers import ChatRequestSerializer
from .services import generate_reply


class ChatbotView(APIView):
    """Floating widget endpoint — keyword bot by default."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]
        user = request.user if request.user.is_authenticated else None

        if user:
            ChatMessage.objects.create(
                user=user,
                sender=ChatMessage.Sender.USER,
                content=message,
            )

        reply = generate_reply(message, user=user)

        bot_msg = None
        if user:
            bot_msg = ChatMessage.objects.create(
                user=user,
                sender=ChatMessage.Sender.BOT,
                content=reply,
            )

        return Response(
            {
                "reply": reply,
                "message_id": bot_msg.id if bot_msg else None,
            },
            status=status.HTTP_200_OK,
        )
