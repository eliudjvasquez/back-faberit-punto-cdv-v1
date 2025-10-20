from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    created_date = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    updated_date = models.DateTimeField(editable=False, null=True)
    deleted_date = models.DateTimeField(editable=False, null=True)
    created_by = models.ForeignKey("self", related_name="created_users", on_delete=models.PROTECT, null=True)
    updated_by = models.ForeignKey("self", related_name="updated_users", on_delete=models.PROTECT, null=True)
    deleted_by = models.ForeignKey("self", related_name="deleted_users", on_delete=models.PROTECT, null=True)


class CreatedUpdatedDeleted(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="%(app_label)s_%(class)s_adder",
                                   on_delete=models.PROTECT, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="%(app_label)s_%(class)s_editor",
                                   on_delete=models.PROTECT, null=True, blank=True)
    updated_date = models.DateTimeField(editable=False, null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="%(app_label)s_%(class)s_deleter",
                                   on_delete=models.PROTECT, null=True, blank=True)
    deleted_date = models.DateTimeField(editable=False, null=True)

    def created_name(self):
        if self.created_by:
            return '%s %s' % (self.created_by.first_name, self.created_by.last_name)
        return None

    def updated_name(self):
        if self.updated_by:
            return '%s %s' % (self.updated_by.first_name, self.updated_by.last_name)
        return None

    def deleted_name(self):
        if self.deleted_by:
            return '%s %s' % (self.deleted_by.first_name, self.deleted_by.last_name)
        return None

    class Meta:
        abstract = True