import secrets

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class Accounts(AbstractBaseUser):

    email = models.EmailField(max_length=255, unique=True)
    confirmation_code = models.IntegerField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    objects = BaseUserManager()

    USERNAME_FIELD = "email"

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        return False

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return False
