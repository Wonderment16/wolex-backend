from rest_framework import serializers
from .models import BankStatement

class StatementUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatement
        fields = ['id', 'user', 'file', 'file_type', 
                "analysis_result", "bank_name", 
                "processed", "uploaded_at"]
        read_only_fields = ['id', 'user', 'analysis_result', 'processed', 'uploaded_at']

def validate_file(self, file):
    allowed_types = ["application/pdf", "text/csv"]
    if file.content_type not in allowed_types:
        raise serializers.ValidationError("Unsupported file type")
    return file
