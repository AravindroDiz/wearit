from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator,MinValueValidator



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
    phone = models.CharField(max_length=15, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    wallet = models.DecimalField(max_digits=20, decimal_places=2, default=0)


    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

class Product(models.Model):
    category = models.ForeignKey('Category',on_delete=models.CASCADE,related_name='products')
    name = models.CharField(max_length=100,null=False,blank=False)
    description = models.TextField(max_length=500,null=False,blank=False)
    image = models.ImageField(upload_to='media/',blank=True,null=True)
    sub_image = models.ManyToManyField('SubImage',blank=True)
    sizes = models.PositiveIntegerField(choices=[(5, '5'), (6, '6'), (7, '7'), (8, '8'),(9, '9'),(10, '10')],default=0)
    quantity = models.PositiveIntegerField(null=False, blank=False)
    base_price = models.PositiveIntegerField(default=0)
    sale_price = models.PositiveIntegerField(default=0)
    status = models.BooleanField(default=True)
    is_sale = models.BooleanField(default=False)


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


class Address(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE,default=True)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    is_default_address = models.BooleanField(default=False)


class Cart(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.PositiveIntegerField(default=0)


class Order(models.Model):
    user = models.ForeignKey(Customer,on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10,decimal_places=2)
    is_paid = models.BooleanField(default=False)
    
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_price = models.DecimalField(max_digits=10,decimal_places=2)
    payment_option = models.CharField(max_length=10,choices=[('pending','pending'),('Cancelled','Cancelled'),('Delivered','Delivered'),('returned','returned')],default='pending')
    is_cancel = models.BooleanField(default=False)
    returned = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)


class Reviews(models.Model):
    user = models.ForeignKey(Customer,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    review = models.TextField(max_length=500)


class Coupon(models.Model):
    code = models.CharField(max_length=50,unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)])
    active = models.BooleanField(default=True)


class ProductOffer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount = models.PositiveIntegerField(help_text="Discount percentage (e.g., 10 for 10%)")
    prod = models.CharField(max_length=200,default=0)

class Refferalcode(models.Model):
    code = models.CharField(max_length=10)
    user = models.ForeignKey(Customer,on_delete=models.CASCADE)
    

class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount = models.PositiveIntegerField(help_text="Discount percentage (e.g., 10 for 10%)")






    