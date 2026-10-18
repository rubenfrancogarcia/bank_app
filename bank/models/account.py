from bank.utils.bank_exception import BankException

class Account:
   
    def __init__(self ):
        self.balance = 0
        

    def withdraw(self, amount):
        if(self.balance - amount < 0):
            raise BankException("Insufficient funds")

        self.balance = self.balance - amount   

    def add(self, amount):
        self.balance += amount    
