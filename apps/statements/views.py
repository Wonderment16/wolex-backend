from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import StatementUploadSerializer
from .services_utils import process_statement
from threading import Thread
from .services.statement_parser import parse_statement
from apps.statements.tasks.process_statement import process_statement_task


# Create your views here.
class StatementUploadView(APIView):
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = StatementUploadSerializer(
            data=request.data,
            context={"request": request},
            )

        def run_async(statement_id):
            process_statement_task(statement_id)

        if serializer.is_valid():
            statement  = serializer.save(user=request.user)
            Thread(target=run_async, args=(statement.id,)).start()
            return Response(
                {
                    "message": "Statement uploaded and is being processed.",
                    "statement_id": statement.id
                }
            )

        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST)
