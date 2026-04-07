from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser

from apps.users.models import BillingAccount
from apps.users.plan import PRICING_NGN
from apps.users.api.serializers import BillingAccountSerializer

def home(request):
    return HttpResponse("Welcome to the Wolex Application!")


def index(request):
    return home(request)

class HealthCheckView(APIView):
    authentication_classes = []

    def get(self, request):
        return Response({
            "status": "ok",
            "service": "wolex_backend"
        })


class PricingView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def _base_context(self):
        account_types = [
            {"code": code, "label": label, "price": PRICING_NGN.get(code)}
            for code, label in BillingAccount.ACCOUNT_TYPES
        ]
        return {
            "currency": "NGN",
            "pricing": PRICING_NGN,
            "account_types": account_types,
        }

    def get(self, request):
        context = self._base_context()
        context.update({"errors": {}, "data": {}})

        if request.accepted_renderer.format == "html":
            return Response(context, template_name="pricing.html")
        return Response(context)

    def post(self, request):
        serializer = BillingAccountSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            billing = serializer.save()
            context = self._base_context()
            context.update(
                {
                    "success": True,
                    "billing": BillingAccountSerializer(billing).data,
                    "data": {},
                    "errors": {},
                }
            )
            if request.accepted_renderer.format == "html":
                return Response(context, template_name="pricing.html", status=201)
            return Response(context["billing"], status=201)

        if request.accepted_renderer.format == "html":
            data = {k: v for k, v in request.data.items() if k != "csrfmiddlewaretoken"}
            context = self._base_context()
            context.update({"errors": serializer.errors, "data": data, "success": False})
            return Response(context, template_name="pricing.html", status=400)

        return Response(serializer.errors, status=400)
    
