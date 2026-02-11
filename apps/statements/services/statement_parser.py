from apps.transactions.services.transaction_service import create_transaction



def parse_statement(statement):
    '''
    Takes a BankStatement instance
    Extracts transaction
    Creates Transaction records
    '''
    user = statement.user

    for row in statement.rows:
        create_transaction(
            user=user,
            transaction_type=row['type'],
            amount=row['amount'],
            description=row['description']
        )
    