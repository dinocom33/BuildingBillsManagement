from django.contrib.auth import get_user_model
from month.models import MonthField

from django.db import models

User = get_user_model()


class Building(models.Model):
    number = models.IntegerField()
    address = models.CharField(max_length=100)

    class Meta:
        unique_together = ('number', 'address')

    def __str__(self):
        return str(self.number)


class Entrance(models.Model):
    name = models.CharField(max_length=100)
    building = models.ForeignKey('Building', on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'building')

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
        # unique_together = ('number', 'building', 'entrance', 'floor', 'owner')

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
        ordering = ['-for_month', 'apartment']

    def __str__(self):
        return str(self.for_month)

    def __unicode__(self):
        return unicode(self.for_month)

    def total_bill(self):
        return self.electricity + self.cleaning + self.elevator_electricity + self.elevator_maintenance + self.entrance_maintenance


class Bill(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='bill')
    entrance = models.ForeignKey(Entrance, on_delete=models.CASCADE, related_name='bill')
    total_electricity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_cleaning = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_elevator_electricity = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_elevator_maintenance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total_entrance_maintenance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    for_month = MonthField('Month', null=True)

    class Meta:
        ordering = ['-for_month']

    def total_bill(self):
        return (self.total_electricity + self.total_cleaning + self.total_elevator_electricity
                + self.total_elevator_maintenance + self.total_entrance_maintenance)

    def __unicode__(self):
        return unicode(self.for_month)

    def __str__(self):
        return str(self.total_electricity)


class TotalMaintenanceAmount(models.Model):
    amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='total_maintenance_amount')
    entrance = models.ForeignKey(Entrance, on_delete=models.CASCADE, related_name='total_maintenance_amount')
    for_month = MonthField('Month', null=True)

    class Meta:
        ordering = ['-for_month']

    def __unicode__(self):
        return unicode(self.for_month)

    def __str__(self):
        return str(self.amount)


class Expense(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='expense')
    entrance = models.ForeignKey(Entrance, on_delete=models.CASCADE, related_name='expense')
    maintenance_total_amount = models.ForeignKey(TotalMaintenanceAmount, on_delete=models.CASCADE,
                                                 related_name='expense')
    name = models.CharField(max_length=100)
    cost = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    for_month = MonthField('Month', null=True)

    class Meta:
        ordering = ['-for_month']

    def __unicode__(self):
        return unicode(self.for_month)

    def __str__(self):
        return str(self.name)


class Message(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='message')
    entrance = models.ForeignKey(Entrance, on_delete=models.CASCADE, related_name='message')
    title = models.CharField(max_length=100)
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return str(self.title)