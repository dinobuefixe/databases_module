from django.db import models

# The Pagila tables the sync command reads, mapped read-only (managed = False).


class Country(models.Model):
    country_id = models.AutoField(primary_key=True)
    country = models.TextField()

    class Meta:
        managed = False
        db_table = "country"


class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    city = models.TextField()
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, db_column="country_id")

    class Meta:
        managed = False
        db_table = "city"


class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, db_column="city_id")

    class Meta:
        managed = False
        db_table = "address"


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    first_name = models.TextField()
    last_name = models.TextField()
    store = models.ForeignKey("Store", on_delete=models.DO_NOTHING, related_name="staff", db_column="store_id")

    class Meta:
        managed = False
        db_table = "staff"

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    address = models.ForeignKey(Address, on_delete=models.DO_NOTHING, db_column="address_id")
    # Pagila has no foreign key constraint on this column, hence db_constraint=False.
    manager = models.ForeignKey(
        Staff, on_delete=models.DO_NOTHING, db_column="manager_staff_id", db_constraint=False, related_name="+"
    )

    class Meta:
        managed = False
        db_table = "store"
