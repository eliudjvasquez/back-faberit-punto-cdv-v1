from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from enticen.models import Application
from initial.models import CreatedUpdatedDeleted, User

class PermissionsGroup(CreatedUpdatedDeleted):
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    application = models.ForeignKey(Application, on_delete=models.PROTECT)
    permission = models.JSONField()

    def __str__(self):
        return f"{self.group.name}"

    def get_group_name(self):
        if self.group:
            return self.group.name
        return None

    def get_application_name(self):
        if self.application:
            return self.application.name
        return None

    class Meta:
        verbose_name = "Group permission"
        verbose_name_plural = "Group permissions"
        ordering = ['group', 'permission']


class Profile(CreatedUpdatedDeleted):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    names = models.CharField(verbose_name="Names", max_length=300)
    father_last_name = models.CharField(verbose_name="Father Last name", max_length=300)
    mother_last_name = models.CharField(verbose_name="Mother Last name", max_length=300)
    address = models.CharField(verbose_name="Address", max_length=300, null=True, blank=True)
    type_document = models.ForeignKey(to='enticen.ParameterDetail', verbose_name="Type document",
                                      related_name="type_doc_user", on_delete=models.PROTECT, null=True, blank=True)
    num_document = models.CharField(verbose_name="Num. Document", max_length=20)
    birthday = models.DateField(verbose_name="Birthday", null=True, blank=True)
    photo = models.ImageField(verbose_name="Photo", upload_to='image/user', null=True, blank=True)
    country = models.ForeignKey(to='enticen.ParameterDetail', verbose_name="Country", related_name="country_user",
                                on_delete=models.PROTECT, null=True,
                                blank=True)
    telephone = models.CharField(verbose_name="Telephone", max_length=15)

    def __str__(self):
        return self.user.username

    def get_fullname(self):
        if self.user:
            return f'{self.user.first_name} {self.user.last_name}'
        return None

    def get_country_name(self):
        if self.country:
            return self.country.name
        return None

    def get_type_document_name(self):
        if self.type_document:
            return self.type_document.string_value
        return None


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        instance.profile.save()


class LoginTrace(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="User", related_name="users",
                             on_delete=models.PROTECT)
    trace = models.JSONField(verbose_name="Trace", null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} {self.user.first_name}"

    def get_username(self):
        if self.user:
            return self.user.username
        return None

    def get_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return None

    class Meta:
        verbose_name = "Login Trace"
        verbose_name_plural = "Logins Trace"
        ordering = ['-id']

