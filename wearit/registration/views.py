import calendar
from django.urls import reverse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User,auth
from django.contrib import messages
from .models import Customer,Category,Product,SizeVariant,SubImage,Address,Cart,Order,OrderItem,Reviews,Coupon,ProductOffer,CategoryOffer
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from datetime import datetime,timedelta
import pyotp
from .otp import sent_otp
from django.http import JsonResponse
import razorpay
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.db.models import Count
import json
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa


def index(request):
    if request.user.is_authenticated:
        return render(request,'index.html',{'homepage':True})
    return render(request,'index.html',{'homepage':True})



def products(request):
    user = request.user
    prod = Product.objects.filter(status = True)
    cart_items = Cart.objects.filter(user=user)
    
    return render(request,'product.html',{'addprod':prod,'products':True,'cart_items':cart_items})


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
        phone = request.POST['phone']
        password = request.POST['password']
        cpassword = request.POST['cpassword']
        if password != cpassword:
            messages.error(request,"Incorrect Password")
        elif Customer.objects.filter(email=email).exists():
            messages.warning(request,"Username already exits!")
            return HttpResponseRedirect(request.path_info)
        else:
            user = Customer.objects.create(first_name = firstname,last_name = lastname,email=email,phone=phone)
            user.set_password(password)
            user.save()
            messages.success(request,'You have been succesfully registered.')
            return HttpResponseRedirect(request.path_info)

    return render(request,'register.html')
    

def productdetails(request,product_id):
    product = get_object_or_404(Product, pk=product_id)
    product_offer = ProductOffer.objects.filter(product=product).first()
    subimg = SubImage.objects.filter(products_id = product_id)
    size_variants = SizeVariant.objects.filter(product=product)
    details = Product.objects.get(id=product_id)
    reviews = Reviews.objects.filter(product=product)

    discounted_price = product.base_price

    if product_offer:
        discount = product_offer.discount
        print(discount)
        original_price = product.base_price
        print(original_price) 
        discounted_price = original_price - discount
        product.sale_price = discounted_price
        print(discounted_price)
        product.save()
        
        
    else:
        discounted_price = product.base_price
        
        print(discounted_price)
    return render(request,'productdetails.html',{'proddetails':details,'product': product,'size_variants': size_variants,'subimg':subimg,'reviews':reviews,'product_offer': product_offer,'discounted_price':discounted_price})


def admin(request):
    return render(request,'adminpanel/admin.html')



def adminpanel(request):

    prod = Product.objects.filter(status = True)
    reviews = Reviews.objects.all()
    products = Product.objects.filter(status=True).count()
    users = Customer.objects.filter(is_active = True).count()
    orders = Order.objects.filter(is_paid = False).count()
    order = OrderItem.objects.all()
    product = Product.objects.all()

    order_items = []
    if request.method == 'POST':
        selected_date = request.POST.get('day')
        selected_month = request.POST.get('month')
        selected_year = request.POST.get('year')
        
        selected_date_str = f"{selected_year}-{selected_month}-{selected_date}"

        try:
            selected_date_obj = datetime.strptime(selected_date_str, "%Y-%m-%d")
            selected_date_obj = timezone.make_aware(selected_date_obj)
            
        
        except ValueError:
            selected_date_obj = None
        

        if selected_date_obj:
            orders_on_date = Order.objects.filter(order_date__date=selected_date_obj.date())
            order_items = OrderItem.objects.filter(order__in=orders_on_date)

        else:
            order_items = []

    date_str = "2023-10-28"  # Replace this with the actual date in the format "YYYY-MM-DD"
    

    return render(request, 'adminpanel/dashboard1.html', {
        'prod': products,
        'usr': users,
        'view': prod,
        'order': orders,
        'orderitems': order_items,
        'reviews': reviews,
        'orders':order,
        'products':product,
        'context':date_str,
    
    
    })

    



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
            cat = Category.objects.get(name=category_name)
            product.category = cat
        except Category.DoesNotExist:
            pass

        product.name = request.POST['name']
        product.quantity = request.POST['quantity']
        product.save()
        return redirect('productview')
    
    return render(request,'adminpanel/editproduct.html',{'editpro':product,'cat': category,'prodcat':productCat})

def userview(request):
    userview = Customer.objects.filter(is_superuser=False)
    return render(request,'adminpanel/userview.html',{'usr':userview})


def offerview(request):
    offerview = Coupon.objects.all()
    return render(request,'offerview.html',{'offer':offerview})

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


def userprofile(request,id):
    user = request.user
    users = Customer.objects.get(id=id)
    order = Order.objects.filter(user_id = users)

    try:
        default_address = Address.objects.get(user=user,is_default_address = True)
    except Address.DoesNotExist:
        default_address=None
    return render(request,'userprofile.html',{'users':users,'default_address': default_address,'order':order})

@login_required
def addaddress(request):
    if request.method == 'POST':
        street_address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('pincode')
        user = request.user
        users = Customer.objects.get(email=user)
        if request.user.is_authenticated and street_address and city and state and postal_code:
            address = Address.objects.create(
                user=request.user,
                street_address=street_address,
                city=city,  
                state=state,
                zip_code=postal_code
            )
            messages.success(request,"Address added succesfully.")
            
            return redirect('userprofile',id = users.id)
    return render(request, 'addaddress.html')


def addressview(request):
    user = request.user
    users = Customer.objects.get(email=user)
    address = Address.objects.filter(user=users)
    return render(request, 'addressview.html', {'address': address})



def editprofile(request):
    user = request.user
    users = Customer.objects.get(email=user)
    if request.method == 'POST':
        users.first_name = request.POST['fname']
        users.last_name = request.POST['lname']
        users.email = request.POST['email']
        users.phone = request.POST['phone']
        users.save()
        return redirect('userprofile',id = users.id)


    return render(request,'editprofile.html',{'users':users})


def addtocart(request,id):
    product = Product.objects.get(id=id)
    user = request.user

    if product.quantity == 0:
        messages.error(request,"This product is out of stock")
        return redirect('productdetails',product_id=product.id)
    else:
        cart_item,created = Cart.objects.get_or_create(user=user,product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        messages.success(request,"Product added succesfully.")
    return redirect('products')


def buynow(request,id):
    product = Product.objects.get(id=id)
    user = request.user
    if product.quantity == 0:
        messages.error(request,"This product is out of stock")
        return redirect('productdetails',product_id=product.id)
    
    else:
        cart_item,created = Cart.objects.get_or_create(user=user,product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    return redirect('cart')

def removefromcart(request, id):
    user = request.user
    cart_item = get_object_or_404(Cart, user=user, id=id)
    cart_item.delete()
    return redirect('home')
    
    

def cart(request): 
    user = request.user
    users = Customer.objects.get(email=user)
    cart_items = Cart.objects.filter(user=users)
    items_num = Cart.objects.filter(user=users).count()
    addre = Address.objects.filter(user=users)
    total = calculatetotal(cart_items)
    

            
    return render(request,'cart.html',{'cart_items':cart_items,'address':addre,'num':items_num,'total':total})


def calculatetotal(cart_items):
    total_price = 0
    for items in cart_items:
        product = items.product
        quantity = items.quantity
        if product.sale_price > 0:
            
            price = product.sale_price
        else:
            price = product.base_price

        item_total = price * quantity
        total_price += item_total
    return total_price


def update_quantity(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)
        user = request.user 
        change = int(request.POST.get('qty'))
        print(change)
        try:
            cart_item = Cart.objects.get(user=user, product=product)
            if change == 1:
                
                cart_item.quantity += 1
                cart_item.save()
            elif change == -1:
                
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart_item.delete()
        except Cart.DoesNotExist:
                    pass

        new_quantity = Cart.objects.get(product=product).quantity
        cart_items = Cart.objects.filter(user=user)
        total = calculatetotal(cart_items)
        return JsonResponse({'new_quantity': new_quantity,'total':total})
    return JsonResponse({'error': 'Invalid request method'})

def checkoutpage(request):
    user = request.user
    cus = Customer.objects.get(email=user)
    items_num = Cart.objects.filter(user=user).count()
    cart_items = Cart.objects.filter(user=user)
    addre = Address.objects.filter(user=user)
    total = calculatetotal(cart_items)
    if request.method == 'POST':
        if 'apply_coupon' in request.POST:  # Check if the "Apply Coupon" button was clicked
            coupon_code = request.POST['coupon_code']
            try:
                # Check if the coupon code is valid and get the discount amount
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.active:
                    discount = coupon.discount
                    total -= discount  # Apply the discount to the total
                    messages.success(request, "Coupon applied successfully.")
                else:
                    messages.error(request, "The coupon is not active.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code. Please try again.")

        elif 'payment_method' :
            payment = request.POST['payment_method']
            if payment == 'cod':
                print(total)
                order = Order.objects.create(user=user,total_price=total)
                order.save()
                for item in cart_items:
                    price = item.product.base_price * item.quantity
                    order_item =OrderItem.objects.create(order=order,product = item.product,quantity = item.quantity,item_price = price)
                    order_item.save()
                if order:
                    cart_items.delete()
                    ordered_items = OrderItem.objects.filter(order=order)
                    for ordered_item in ordered_items:
                        product = ordered_item.product
                        quantity_ordered = order_item.quantity
                        product.quantity -= quantity_ordered
                        product.save()
                        messages.success(request,"Order placed succesfully !")
                        return redirect('successpage')
        elif payment == 'upi':
            client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY,settings.RAZORPAY_API_SECRET))
            amount = int(total*100)
            payment = client.order.create({'amount':amount,'currency':'INR','payment_capture':'1'})

            order = Order.objects.create(user=user,total_price=total)
            order.save()
            for item in cart_items:
                price = item.product.base_price * item.quantity
                order_item =OrderItem.objects.create(order=order,product = item.product,quantity = item.quantity,item_price = price)
                order_item.save()
            if order:
                cart_items.delete()
                ordered_items = OrderItem.objects.filter(order=order)
                for ordered_item in ordered_items:
                    product = ordered_item.product
                    quantity_ordered = order_item.quantity
                    product.quantity -= quantity_ordered
                    product.save()
                    messages.success(request,"Order placed succesfully !")
                    return render(request,'razorpay.html',{'user':cus,'payment':payment,'order':order})
    else:
        messages.error(request,"Please select a payment option")   
    

    return render(request,'checkoutpage.html',{'cart_items':cart_items,'addre':addre,'total':total,'num':items_num})

@csrf_exempt
def successpage(request):
    return render(request,'successpage.html')


@login_required
def orderview(request):

    user = request.user
    if not user.is_authenticated:
        return redirect('loginn')
    
    try:

        users = Customer.objects.get(email=user)
    except Customer.DoesNotExist:
        user = None

    order_items = OrderItem.objects.filter(order__user=user)

    return render(request,'ordersview.html',{'order_items': order_items,'users':users})


def cancel_order(request,id):
    if request.user.is_authenticated:
    
        orderitem = get_object_or_404(OrderItem,id=id)
        if orderitem.is_cancel:
            messages.error(request,'This order item has already been canceled.')
        else:
            orderitem.payment_option = 'Cancelled'
            orderitem.is_cancel = True
            orderitem.save()
            
            orderitem.product.quantity += orderitem.quantity
            orderitem.product.save()

            messages.success(request,'Order item canceled successfully.')
            return redirect('orderview')
        
    
    return render(request,'ordersview.html',{'order':orderitem})


def return_order(request,id):
    if request.user.is_authenticated:
    
        orderitem = get_object_or_404(OrderItem,id=id)

        if orderitem.payment_option != 'returned':
            orderitem.payment_option = 'returned'
            orderitem.is_cancel = True
            orderitem.save()
            
            orderitem.product.quantity += orderitem.quantity
            orderitem.product.save()

            messages.success(request,'Order item returned successfully.')
            return redirect('orderview')
        
    
    return render(request,'ordersview.html')


def order_delivered(request,id):
    order = get_object_or_404(OrderItem,id=id)
    if order.payment_option != 'Delivered':
        order.payment_option = 'Delivered'
        order.save()
        return redirect('adminorder')
    

def adminorder(request):
    orderitem = OrderItem.objects.all()
    user = Customer.objects.all()
    return render(request,'adminpanel/order.html',{'orderitem':orderitem,'user':user})




def reviews(request,id):
    user = request.user
    users = Customer.objects.get(email = user)
    product = get_object_or_404(Product,id=id)
    if request.method == 'POST':
        review = request.POST['message']
        post = Reviews.objects.create(review=review,user = users,product=product)
        post.save()
        return redirect('productdetails',product_id=product.id)
    return redirect(request,'productdetails.html',{'users':users,'product':product,'reviews':reviews})



def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')

        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
        except Coupon.DoesNotExist:
            return render(request, 'cart.html', {'error_message': 'Invalid or expired coupon code'})
        
        user_cart, created = Cart.objects.get_or_create(user=request.user)

        for cart_item in user_cart.items.all():
            discounted_price = cart_item.product.base_price * (1 - (coupon.discount / 100))
            cart_item.product.base_price = discounted_price
            cart_item.product.save()

        return redirect('view_cart')

def add_coupon(request):
    if request.method == 'POST':
        code = request.POST['code']
        valid_from = request.POST['valid_from']
        valid_to = request.POST['valid_to']
        discount = request.POST['discount']

        coupon = Coupon.objects.create(code = code,valid_from = valid_from,valid_to = valid_to,discount = discount)
        coupon.save()
        return redirect('adminpanel')
    return render(request,'addcoupon.html')


def get_discount_price(request, id):
    product = Product.objects.get(pk=id)
    product_offer = ProductOffer.objects.filter(product=product).first()
    
    if product_offer:
        discount = product_offer.discount
        discounted_price = product.base_price * (1 - discount/100)
    else:
        discounted_price = product.base_price

    context = {
        'discounted_price': discounted_price,
    }

    return render(request, 'productdetails.html', context)

def salesreport(request):
    products = OrderItem.objects.all()

    context = {
        'products':products
    }

    return render(request,'salesreport.html',context)
    

def venue_pdf(request):
        selected_date = datetime.now()
        products = OrderItem.objects.filter(order__order_date__date=selected_date)
        template_path = 'pdfreport.html'
        context = {'products': products}

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

        template = get_template(template_path)
        html = template.render(context)

        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response


def add_offer(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        discount = request.POST['discount']
        category_name = request.POST.get('category')

        try:
            product = Product.objects.get(name=category_name)
            offer = ProductOffer.objects.create(title=title, description=description, discount=discount, product=product)
            offer.save()
            
            return redirect('adminpanel') 
        except Product.DoesNotExist:
            pass

    product = Product.objects.all()
    return render(request, 'addproductoffer.html', {'product': product})


def productofferview(request):
    prodoffer = ProductOffer.objects.all()
    return render(request,'productofferview.html',{'prodoffer':prodoffer})


def search_products(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query)
    return render(request,'search_results.html',{'product':products})

# def sort_products(request):


def adminlogout(request):
    auth.logout(request)
    return redirect('loginn')




