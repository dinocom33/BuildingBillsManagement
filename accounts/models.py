from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from building.models import Building, Entrance, Apartment
from .managers import CustomUserManager


class User(AbstractUser):
    username = None
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    building = models.ForeignKey(Building, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='building')
    entrance = models.ForeignKey(Entrance, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='entrance')
    apartment = models.ForeignKey(Apartment, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='apartment')

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.email
