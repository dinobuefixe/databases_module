from django.db import models


class Hello(models.Model):
    msg = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hello"
