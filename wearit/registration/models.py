from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Customer(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Add your custom fields here

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

class Product(models.Model):
    category = models.ForeignKey('Category',on_delete=models.CASCADE,related_name='products')
    name = models.CharField(max_length=100,null=False,blank=False)
    description = models.TextField(max_length=500,null=False,blank=False)
    quantity = models.IntegerField(null=False,blank=False)
    base_price = models.IntegerField(default=0)
    image = models.ImageField(upload_to='media/',blank=True,null=True)
    sub_image = models.ManyToManyField('SubImage',blank=True)
    status = models.BooleanField(default=True)
    trending = models.BooleanField(default=True)


    def __str__(self):
        return self.name
    
class SubImage(models.Model):
    products =  models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_sub_images/')
    
    

class Category(models.Model):
    name = models.CharField(max_length=100,null=False,blank=False)
    discription = models.TextField(default=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SizeVariant(models.Model):
    product = models.ForeignKey('Product',on_delete=models.CASCADE,related_name='variants')
    size = models.CharField(max_length=100,null=False,blank=False)
    price_adjustment = models.IntegerField(default=0)

    def __str__(self):
        return self.name
