from django.test import TestCase
from apps.users.models import User, Balance
from apps.transactions.models import Transaction
from apps.transactions.services.transaction_service import create_transaction


# Create your tests here.
class TransactionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email="test@wolex.com")
        self.balance = Balance.objects.create(user=self.user)

    def test_create_earned_transaction(self):
        transaction = create_transaction(
            user=self.user,
            transaction_type='EARNED',
            amount=100.00,
            description='Test Earned Transaction'
        )
        self.assertEqual(transaction.transaction_type, 'EARNED')
        self.assertEqual(transaction.amount, 100.00)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.amount, 100.00)

    def test_create_purchased_transaction(self):
        # First, create an earned transaction to have some balance
        create_transaction(
            user=self.user,
            transaction_type='EARNED',
            amount=150.00,
            description='Initial Earned Transaction'
        )
        transaction = create_transaction(
            user=self.user,
            transaction_type='PURCHASED',
            amount=50.00,
            description='Test Purchased Transaction'
        )
        self.assertEqual(transaction.transaction_type, 'PURCHASED')
        self.assertEqual(transaction.amount, 50.00)
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.amount, 100.00)  # 150 - 50 = 100