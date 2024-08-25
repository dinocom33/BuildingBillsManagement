from django.db import models


class Building(models.Model):
    number = models.IntegerField()
    address = models.CharField(max_length=100)
    num_of_entrances = models.IntegerField()

    def __str__(self):
        return str(self.number)


class Entrance(models.Model):
    name = models.CharField(max_length=100)
    building = models.ForeignKey('Building', on_delete=models.CASCADE)
    floors = models.IntegerField()
    num_of_apartments = models.IntegerField()

    def __str__(self):
        return self.name


class Apartment(models.Model):
    building = models.ForeignKey('Building', on_delete=models.CASCADE)
    entrance = models.ForeignKey('Entrance', on_delete=models.CASCADE)
    floor = models.IntegerField()
    number = models.IntegerField()

    def __str__(self):
        return str(self.number)


class Bill(models.Model):
    apartment = models.ForeignKey('Apartment', on_delete=models.CASCADE)
    electricity = models.FloatField()
    cleaning = models.FloatField()
    elevator_electricity = models.FloatField()
    elevator_maintenance = models.FloatField()
    entrance_maintenance = models.FloatField(default=10)

    def __str__(self):
        return str(self.apartment)

    def total_bill(self):
        return self.electricity + self.cleaning + self.elevator_electricity + self.elevator_maintenance + self.entrance_maintenance
