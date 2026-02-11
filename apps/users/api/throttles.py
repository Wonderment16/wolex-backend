from rest_framework.throttling import UserRateThrottle

class ChatbotUserThrottle(UserRateThrottle):
    scope = 'chatbot'