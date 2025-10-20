from django.db import models
from cryptography.fernet import Fernet
from django.conf import settings
from decimal import Decimal

fernet = Fernet(settings.FERNET_KEY)

class EncryptedDecimalField(models.TextField):
    def __init__(self, *args, blank=True, null=True, **kwargs):
        self.blank = blank
        self.null = null
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return Decimal(fernet.decrypt(value.encode()).decode())

    def to_python(self, value):
        if value is None or isinstance(value, Decimal):
            return value
        try:
            return Decimal(fernet.decrypt(value.encode()).decode())
        except Exception:
            return value  # puede ser útil en migrations o raw SQL

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, float):  # convierte floats a Decimal
            value = Decimal(str(value))
        return fernet.encrypt(str(value).encode()).decode()
    
class EncryptedField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return fernet.decrypt(value.encode()).decode()
        except Exception:
            return value

    def to_python(self, value):
        if value is None or isinstance(value, str):
            return value
        try:
            return fernet.decrypt(value.encode()).decode()
        except Exception:
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return fernet.encrypt(value.encode()).decode()