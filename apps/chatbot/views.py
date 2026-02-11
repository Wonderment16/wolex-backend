from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.permissions import IsAuthenticated
from .serializers import ChatbotMessageSerializer


class ChatbotEndpoint(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chatbot'

    def get(self, request):
        return Response({
            "status": "ok",
            "message": "Chatbot endpoint is available. POST a JSON body with {'message': '...'}",
        })

    def post(self, request):
        serializer = ChatbotMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data["message"]

        # Placeholder behavior: echo back the user's message.
        return Response({
            "reply": f"You said: {user_message}",
        })

class UserContextView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'chatbot'

    def get(self, request):
        user = request.user
        
        return Response({
            'balance': user.balance.amount,
            'total_transactions': user.transactions.count(),
            'recent_transactions': [
                {
                    'amount': t.amount,
                    'type': t.transction_type,
                    'description': t.description,
                }
                for t in user.transactions.order_by('-created_at')[:5]
            ]
        })
    

