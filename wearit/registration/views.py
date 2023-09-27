from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User,auth
from django.contrib import messages
from .models import Customer,Category,Product,SizeVariant,SubImage
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from datetime import datetime,timedelta
import pyotp
from .otp import sent_otp



def index(request):
    if request.user.is_authenticated:
        return render(request,'index.html',{'homepage':True})
    return render(request,'index.html',{'homepage':True})



def products(request):
    prod = Product.objects.filter(status = True)
    return render(request,'product.html',{'addprod':prod,'products':True})


def loginn(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']
        user = Customer.objects.filter(email = username)
        
        if not user.exists():
            messages.warning(request,'Account Not Found !')
            return HttpResponseRedirect(request.path_info)

        
        user = authenticate(request,email=username,password=password)
        if user is not None:
            if user.is_active:
                if sent_otp(request):
                    request.session['username'] = username
                    return redirect('otp')
        
            else:
                messages.warning(request,'Account is Blocked !')

        else:
            messages.warning(request,'Invalid Credentials !')


    return render(request, 'login.html',{'login':True})

def otp(request):
    if request.method == 'POST':
        verify_otp = request.POST.get('verify_otp') 

        if 'username' in request.session:
            username = request.session['username']
        else:
            messages.error(request, 'Username not found in session')
            return redirect('loginn')

        otp_secret_key = request.session['otp_secret_key']
        otp_valid_until = request.session['otp_valid_date']
        if otp_secret_key and otp_valid_until:
            valid_until = datetime.fromisoformat(otp_valid_until)
            if valid_until > datetime.now():
                totp = pyotp.TOTP(otp_secret_key, interval=60)
                if totp.verify(verify_otp):
                    try:
                        user = Customer.objects.get(email=username)
                        login(request, user)
                        del request.session['otp_secret_key']
                        del request.session['otp_valid_date']
                        return redirect('home')
                    except Customer.DoesNotExist:
                        messages.error(request, 'User not found')
                else:
                    messages.error(request, 'Invalid one-time password')
            else:
                messages.error(request, 'One-time password expired')
        else:
            messages.error(request, 'Something went wrong')

    return render(request, 'otp.html')

def register(request):
    if request.method == "POST":
        firstname = request.POST['fname']
        lastname = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        cpassword = request.POST['cpassword']
        if password != cpassword:
            messages.error(request,"Incorrect Password")
        elif Customer.objects.filter(email=email).exists():
            messages.warning(request,"Username already exits!")
            return HttpResponseRedirect(request.path_info)
        else:
            user = Customer.objects.create(first_name = firstname,last_name = lastname,email=email)
            user.set_password(password)
            user.save()
            messages.success(request,'You have been succesfully registered.')
            return HttpResponseRedirect(request.path_info)

    return render(request,'register.html')
    

def productdetails(request,product_id):
    product = Product.objects.get(id=product_id)
    subimg = SubImage.objects.filter(products_id = product_id)
    size_variants = SizeVariant.objects.filter(product=product)
    details = Product.objects.get(id=product_id)
    return render(request,'productdetails.html',{'proddetails':details,'product': product,'size_variants': size_variants,'subimg':subimg})


def admin(request):
    return render(request,'adminpanel/admin.html')


def adminpanel(request):

    prod = Product.objects.filter(status = True)
   
    products = Product.objects.filter(status=True).count()
    users = Customer.objects.filter(is_active = True).count()
    return render(request,'adminpanel/dashboard1.html',{'prod':products, 'usr' : users,'view':prod})



def productview(request):
    proview = Product.objects.filter(status=True)
    category = Category.objects.all()
    return render(request,'adminpanel/productview.html',{'view':proview,'cat':category})


def filter(request,id):
    proview = Product.objects.filter(category_id = id,status=True)
    category = Category.objects.all()

    return render(request,'adminpanel/productview.html',{'view':proview,'cat':category})

def addproduct(request):
    if request.method == 'POST':
        name = request.POST['name']
        quantity = request.POST['quantity'] 
        price = request.POST['price']    
        image = request.FILES['image']
        category = Category.objects.get(name=request.POST['category'])
        discription = request.POST['discription']
        if Product.objects.filter(name = name).exists():
            messages.info(request,"Product Already Exist !")
            return redirect('addproduct')
        else:
            product = Product.objects.create(name=name,image=image,quantity=quantity,base_price = price,category= category,description=discription)
            product.save()
            for file in request.FILES.getlist('subimages'):
                SubImage.objects.create(products=product,image=file)
            messages.success(request,'Product added successfully.')
            return redirect('adminpanel')

    cat = Category.objects.all()
    return render(request,'adminpanel/addproduct.html',{'category': cat})


def addcategory(request):
    if request.method == 'POST':
        catname = request.POST['name']
        discription = request.POST['discription']
        if Category.objects.filter(name = catname).exists():
            messages.info(request,"Category already exists!")
            return redirect('addcategory')
        else:
            cat = Category.objects.create(name = catname,discription=discription)
            cat.save()
            messages.success(request,"Category added successfully!")
            return redirect('adminpanel')
    category = Category.objects.all()
    return render(request,'adminpanel/addcategory.html',{'cat':category})

def categoryview(request):
    catview = Category.objects.all()
    return render(request,'adminpanel/categoryview.html',{'cat':catview})

def editcategory(request,id):
    category = Category.objects.get(id=id)
    if request.method == 'POST':
        category.name = request.POST['name']
        category.discription = request.POST['discription']
        if Category.objects.filter(name = category.name).exists():
            messages.info(request,"Name not available")
            return redirect('adminpanel')
        else:
            category.save()
            return redirect('adminpanel')
    return render(request,'adminpanel/editcategory.html',{'cat':category})


def addsize(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        size = request.POST['size']
        price = request.POST['price']
        if SizeVariant.objects.filter(product=product, size=size).exists():
            messages.warning(request, 'Size already exists!')
            return redirect('addsize')
        else:
            SizeVariant.objects.create(product=product, size=size, price_adjustment=price)
            messages.success(request, 'Size added successfully!')
            return redirect('adminpanel')

    return render(request, 'adminpanel/addsize.html', {'product': product})

def deletecategory(request, id):
    try:
        category = Category.objects.get(id=id)
        
        if category.products.all().exists():
            messages.warning(request, "Cannot delete category with associated products.")
            return redirect('adminpanel')
        
        category.delete()
        messages.success(request, "Category deleted successfully.")
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
    
    return redirect('adminpanel')


def deleteproduct(request, id):
    try:
        product = Product.objects.get(id=id)
        if product.status: 
            product.status = False 
        else: 
            product.status = True 
        product.save()
        return redirect('productview')
    except Product.DoesNotExist:

        pass


def editproduct(request,id):
    product = Product.objects.get(id=id)
    category = Category.objects.all()
    productCat = Category.objects.get(id=product.category_id)
    
    if request.method == 'POST':
        category_name = request.POST.get('category')
        
        try:
            cat = Category.objects.get(name='category')
            product.category = cat
        except Category.DoesNotExist:
            product.name = request.POST['name']
            product.quantity = request.POST['quantity']
            product.save()
        return redirect('productview')
    
    return render(request,'adminpanel/editproduct.html',{'editpro':product,'cat': category,'prodcat':productCat})

def userview(request):
    userview = Customer.objects.filter(is_superuser=False)
    return render(request,'adminpanel/userview.html',{'usr':userview})


def blockuser(request,id):
    block = Customer.objects.get(id=id)
    if block.is_active:
        block.is_active = False
        block.save()
    else:
        block.is_active= True
        block.save()
    return redirect('userview')

def blockcategory(request,id):
    category = Category.objects.get(id=id)
    if category.status:
        category.status = False
        category.save()
    else:
        category.status = not category.status
        category.save()
    return redirect('categoryview')



def adminlogout(request):
    auth.logout(request)
    return redirect('loginn')




