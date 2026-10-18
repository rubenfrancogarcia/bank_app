class Loan:
    def __init__(self, principal, term, rate):
        self._principal = principal
        self._term = term
        self._rate = rate

    
    def pay(self, amount):
        self._principal =- amount
    
    @property
    def principal(self):
        return self.principal

    @principal.setter
    def setPrincipal(self, amount):
        self._principal += amount

    @property
    def term(self):
        return self._term;    

    @term.setter
    def setTerm(self, term):
        self._term = term

    @property
    def rate(self):
        return self._rate    

    @rate.setter
    def setRate(self, rate):
        self._rate = rate