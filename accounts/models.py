from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
# Create your models here.

class MyAccountManager(BaseUserManager):

    def create_user(self,first_name,last_name,username,email,password):
        if not email:
            raise ValueError('NOT PROVIDED OR SEEMS WRONG')
        if not username:
            raise ValueError('USERNAME IS MANDATORY')

        user = self.model(first_name = first_name,
                        last_name = last_name,
                        email = self.normalize_email(email),
                        username = username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,first_name,last_name,email,username,password):
        user = self.create_user(first_name = first_name,
                                last_name = last_name,
                                email = self.normalize_email(email),
                                username = username,
                                password = password,)

        user.is_active = True
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractUser):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    username = models.CharField(max_length=100)
    email = models.EmailField(max_length=100,unique=True)
    phone = models.CharField(max_length=20)

    #mandatory required fields
    date_created = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm,obj=None):
        return self.is_admin

    def has_module_prems(self,add_lable):
        return True

class UserProfile(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(max_length=200,blank=True)
    address_line_2 = models.CharField(max_length=200,blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    profile_picture = models.ImageField(blank=True,upload_to='userprofile')

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'
