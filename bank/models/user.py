class User: 
    def __init__(self, firstName, lastName, email):
        self._firstName = firstName
        self._lastName = lastName
        self._email = email

    @property
    def firstName(self):
        return self._firstName        

    @firstName.setter
    def setFirstName(self, firstName):
        self._firstName = firstName    

    @property
    def lastName(self):
        return self._lastName;

    @lastName.setter
    def setLastName(self, lastName):
        self._lastName = lastName

    @property
    def email(self):
        return self._email

    @email.setter
    def setEmail(self, email):
        self._email = email    