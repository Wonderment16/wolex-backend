from .models import BankStatement

def process_statement(BankStatement):
    """
    Takes a Statement instance,
    extracts data from the uploaded file,
    analyzes it,
    and stores structured results.
    """

    # Placeholder for extraction logic
    # PDF / CSV / XLSX handling will live here

    analysis_result = {
        "status": "received",
        "message": "Statement uploaded successfully. Analysis pending."
    }

    BankStatement.analysis_data = analysis_result
    BankStatement.processed = True
    BankStatement.save()

    return analysis_result
