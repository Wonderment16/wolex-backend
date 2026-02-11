from apps.statements.services.statement_parser import parse_statement
from apps.statements.models import BankStatement 

def process_statement_task(statement_id):
    statement = BankStatement.objects.get(id=statement_id)
    if statement.processed:
        return
    
    parse_statement(statement)

