from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# class User(AbstractUser):
#     email = models.EmailField(unique=True)
#     name = models.CharField(max_length=150)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']  # email must NOT be here

#     def set_password(self, raw_password):
#         self.password = make_password(raw_password)
#         self.save()

#     def check_password(self, raw_password):
#         return check_password(raw_password, self.password)
    
#     def __str__(self):
#         return self.email

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email must NOT be here
    
    def __str__(self):
        return self.email
    
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Department(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

