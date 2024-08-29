from django.utils import timezone
from django.contrib.auth import get_user_model
from month.models import MonthField

from django.db import models

User = get_user_model()


class Building(models.Model):
    number = models.IntegerField()
    address = models.CharField(max_length=100)

    # num_of_entrances = models.IntegerField()

    def __str__(self):
        return str(self.number)


class Entrance(models.Model):
    name = models.CharField(max_length=100)
    building = models.ForeignKey('Building', on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    # floors = models.IntegerField()
    # num_of_apartments = models.IntegerField()

    def __str__(self):
        return self.name


class Apartment(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='apartments')
    entrance = models.ForeignKey(Entrance, on_delete=models.CASCADE, related_name='apartments')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner')
    floor = models.IntegerField()
    number = models.IntegerField()

    class Meta:
        ordering = ['number']

    # bill = models.ForeignKey('ApartmentBill', on_delete=models.CASCADE, null=True, related_name='apartment')

    def __str__(self):
        return str(self.number)


class ApartmentBill(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='bill')
    electricity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    cleaning = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    elevator_electricity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    elevator_maintenance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    entrance_maintenance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    change = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    for_month = MonthField('Month', null=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ['apartment__number']

    def __str__(self):
        return str(self.for_month)

    def __unicode__(self):
        return unicode(self.for_month)

    def total_bill(self):
        return self.electricity + self.cleaning + self.elevator_electricity + self.elevator_maintenance + self.entrance_maintenance


class Bill(models.Model):
    total_electricity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_cleaning = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_elevator_electricity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_elevator_maintenance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_entrance_maintenance = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.total_electricity)
