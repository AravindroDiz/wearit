import calendar
from django.urls import reverse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User,auth
from django.contrib import messages
from .models import Customer,Category,Product,SubImage,Address,Cart,Order,OrderItem,Reviews,Coupon,ProductOffer,Refferalcode
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
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
from django.http import Http404



def index(request):
    if request.user.is_authenticated:
        return render(request,'index.html',{'homepage':True})
    return render(request,'index.html',{'homepage':True})


@login_required(login_url='loginn')
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
        if user is not None and not user.is_staff:
            if user.is_active:
                login(request,user)
                request.session['username'] = username
                return redirect('home')
                    
                    
                # if sent_otp(request):
                    
        
            else:
                messages.warning(request,'Account is Blocked !')

        else:
            messages.warning(request,'Invalid Credentials !')


    return render(request, 'login.html',{'login':True})

# def otp(request):
#     if request.method == 'POST':
#         verify_otp = request.POST.get('verify_otp') 

#         if 'username' in request.session:
#             username = request.session['username']
#         else:
#             messages.error(request, 'Username not found in session')
#             return redirect('loginn')

#         otp_secret_key = request.session['otp_secret_key']
#         otp_valid_until = request.session['otp_valid_date']
#         if otp_secret_key and otp_valid_until:
#             valid_until = datetime.fromisoformat(otp_valid_until)
#             if valid_until > datetime.now():
#                 totp = pyotp.TOTP(otp_secret_key, interval=60)
#                 if totp.verify(verify_otp):
#                     try:
#                         user = Customer.objects.get(email=username)
#                         login(request, user)
#                         del request.session['otp_secret_key']
#                         del request.session['otp_valid_date']
#                         return redirect('home')
#                     except Customer.DoesNotExist:
#                         messages.error(request, 'User not found')
#                 else:
#                     messages.error(request, 'Invalid one-time password')
#             else:
#                 messages.error(request, 'One-time password expired')
#         else:
#             messages.error(request, 'Something went wrong')

#     return render(request, 'otp.html')

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
            return redirect('loginn')

    return render(request,'register.html')



    
@login_required(login_url='loginn')
def productdetails(request,product_id):
    product = get_object_or_404(Product, pk=product_id)
    product_offer = ProductOffer.objects.filter(product=product).first()
    subimg = SubImage.objects.filter(products_id = product_id)
    details = Product.objects.get(id=product_id)
    reviews = Reviews.objects.filter(product=product)
    sizes = Product._meta.get_field('sizes').choices

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
    return render(request,'productdetails.html',{'proddetails':details,'product': product,'subimg':subimg,'reviews':reviews,'product_offer': product_offer,'discounted_price':discounted_price,'sizes': sizes})


def admin(request):
    if request.method == 'POST':
        username = request.POST['email']
        password = request.POST['password']
    try:
        user = authenticate(request, email=username, password=password)

        if user is not None:
            if user.is_staff:
                request.session['username'] = username
                login(request, user)
                return redirect('adminpanel')
            else:
                messages.error(request, 'Login using user login!')
                return redirect('loginn')
    except:
            pass

    return render(request, 'adminpanel/admin.html')

@staff_member_required(login_url='admin')
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

    


@login_required(login_url='admin')
def productview(request):
    category = Category.objects.all()
    product = Product.objects.filter(status=True)
    user = request.user
    if user.is_active:
        search = request.POST.get('search')
        if search:
            product = Product.objects.filter(name__icontains = search)
    return render(request,'adminpanel/productview.html',{'view':product,'cat':category})


@login_required(login_url='admin')
def filter(request,id):
    proview = Product.objects.filter(category_id = id,status=True)
    category = Category.objects.all()

    return render(request,'adminpanel/productview.html',{'view':proview,'cat':category})


@login_required(login_url='admin')
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



@login_required(login_url='admin')
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


@login_required(login_url='admin')
def categoryview(request):
    catview = Category.objects.all()
    return render(request,'adminpanel/categoryview.html',{'cat':catview})


@login_required(login_url='admin')
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


@login_required(login_url='admin')
def addsize(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        sizes = request.POST['size']
        variant_prices = request.POST['variant_price']
        variant_quantities = request.POST['variant_quantity']
        product_variant = SizeVariant.objects.create(product=product, size=sizes, base_price=variant_prices, quantity=variant_quantities)
        product_variant.save()
        messages.success(request, 'Size added successfully.')
        return redirect('adminpanel')

    return render(request, 'adminpanel/addsize.html', {'product': product})


@login_required(login_url='admin')
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


@login_required(login_url='admin')
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

@login_required(login_url='admin')
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

@login_required(login_url='admin')
def userview(request):
    cus = Customer.objects.all()
    user = request.user
    if user.is_active:
        search = request.POST.get('search')
        if search:
            cus = Customer.objects.filter(first_name__icontains = search)
        else:
            cus = Customer.objects.all()
    return render(request,'adminpanel/userview.html',{'usr':cus})


@login_required(login_url='admin')
def offerview(request):
    offerview = Coupon.objects.all()
    return render(request,'offerview.html',{'offer':offerview})

@login_required(login_url='admin')
def blockuser(request,id):
    block = Customer.objects.get(id=id)
    if block.is_active:
        block.is_active = False
        block.save()
    else:
        block.is_active= True
        block.save()
    return redirect('userview')


@login_required(login_url='admin')
def blockcategory(request,id):
    category = Category.objects.get(id=id)
    if category.status:
        category.status = False
        category.save()
    else:
        category.status = not category.status
        category.save()
    return redirect('categoryview')

@login_required(login_url='loginn')
def userprofile(request,id):
    user = request.user
    users = Customer.objects.get(id=id)
    order = Order.objects.filter(user_id = users)

    try:
        default_address = Address.objects.get(user=user,is_default_address = True)
    except Address.DoesNotExist:
        default_address=None
    return render(request,'userprofile.html',{'users':users,'default_address': default_address,'order':order})

@login_required(login_url='loginn')
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

@login_required(login_url='loginn')
def addressview(request):
    user = request.user
    users = Customer.objects.get(email=user)
    address = Address.objects.filter(user=users)
    return render(request, 'addressview.html', {'address': address})


@login_required(login_url='loginn')
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


@login_required(login_url='loginn')
def addtocart(request,id):
    if request.method == 'POST':
        product = Product.objects.get(id=id)
        user = request.user
        size = request.POST.get('size')

        if product.quantity == 0:
            messages.error(request,"This product is out of stock")
            return redirect('productdetails',product_id=product.id)
        else:
            cart_item,created = Cart.objects.get_or_create(user=user,product=product,size=size)
            if not created:
                cart_item.quantity += 1
                cart_item.save()
                
            messages.success(request,"Product added succesfully.")
    product = Product.objects.get(id=id)
    return redirect('cart')

@login_required(login_url='loginn')
def buynow(request,id):
    if request.method == 'POST':
        product = Product.objects.get(id=id)
        user = request.user
        size = request.POST.get('size')

        if product.quantity == 0:
            messages.error(request,"This product is out of stock")
            return redirect('productdetails',product_id=product.id)
        else:
            cart_item,created = Cart.objects.get_or_create(user=user,product=product,size=size)
            if not created:
                cart_item.quantity += 1
                cart_item.save()
                
            messages.success(request,"Product added succesfully.")
    product = Product.objects.get(id=id)
    return redirect('cart')

@login_required(login_url='loginn')
def removefromcart(request, id):
    user = request.user
    cart_item = get_object_or_404(Cart, user=user, id=id)
    cart_item.delete()
    return redirect('cart')
    
    
@login_required(login_url='loginn')
def cart(request): 
    user = request.user
    users = Customer.objects.get(email=user)
    if not Address.objects.filter(user=users).exists():
        messages.warning(request, 'Please add an address to checkout !')

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


@login_required(login_url='loginn')
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


@login_required(login_url='loginn')
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
                        return redirect('successpage')
            elif payment == 'upi':
                client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY,settings.RAZORPAY_API_SECRET))
                amount = int(total*100)
                payment = client.order.create({'amount':amount,'currency':'INR','payment_capture':'1'})

                order = Order.objects.create(user=user,total_price=total)
                
                order.save()
                for item in cart_items:
                    price = item.product.base_price * item.quantity
                    order_item =OrderItem.objects.create(order=order,product = item.product,quantity = item.quantity,item_price = price,is_paid=True)
                    order_item.save()
                if order:
                    cart_items.delete()
                    ordered_items = OrderItem.objects.filter(order=order)
                    for ordered_item in ordered_items:
                        product = ordered_item.product
                        quantity_ordered = order_item.quantity
                        product.quantity -= quantity_ordered
                        product.save()
                        return render(request,'razorpay.html',{'user':cus,'payment':payment,'order':order})   

    return render(request,'checkoutpage.html',{'cart_items':cart_items,'addre':addre,'total':total,'num':items_num})

@csrf_exempt
def successpage(request):
    try:
        # Your existing code
        product = ProductOffer.objects.all()
        latest_order = Order.objects.filter(user=request.user).latest('order_date')
        cart_items = OrderItem.objects.filter(order=latest_order)

        total = 0
        deduction = 0
        total_amount = 0  

        for item in cart_items:
            total += item.item_price
            try:
                product_offer = ProductOffer.objects.get(product=item.product_id)
                deduction = product_offer.discount
                total_amount = item.item_price - deduction
            except ProductOffer.DoesNotExist:
                print("No offer for product:", item.product_id)

        context = {
            'cart_items': cart_items,
            'total': total,
            'deduction': deduction,
            'total_amount': total_amount
        }

        return render(request, 'successpage.html', context)

    except Order.DoesNotExist:
        # Handle the case when there is no order for the user
        raise Http404("No order found for the user.")



@login_required(login_url='loginn')
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

@login_required(login_url='loginn')
def cancel_order(request,id):
    order = get_object_or_404(OrderItem, id=id)
    user = request.user
    cus = Customer.objects.get(email = user)
    if order.is_paid:
        total_amount = order.item_price
        cus.wallet += total_amount
        cus.save()
        order.is_cancel = True
        order.item_price = 0
        order.payment_option = 'Cancelled'
        order.save()
        product = order.product
        product.quantity += order.quantity
        product.save()
        messages.success(request, 'Order cancelled!')
        return redirect('orderview')
    else:
        order.is_cancel = True
        order.payment_option = 'Cancelled'
        order.save()
        product = order.product
        product.quantity += order.quantity
        product.save()
        return redirect('orderview')

@login_required(login_url='loginn')
def return_order(request,id):
    user = request.user
    customer = Customer.objects.get(email = user)
    if request.user.is_authenticated:
    
        orderitem = get_object_or_404(OrderItem,id=id)

        if orderitem.payment_option != 'returned':
            orderitem.payment_option = 'returned'
            orderitem.is_cancel = True
            orderitem.save()
            
            orderitem.product.quantity += orderitem.quantity
            orderitem.product.save()

            if orderitem.is_paid:
                amount = orderitem.item_price
                customer.wallet += amount
                customer.save()
                print(amount)

                orderitem.item_price = 0   
                orderitem.save()

            messages.success(request,'Order item returned successfully.')
            return redirect('orderview')
        
    
    return render(request,'ordersview.html')


def order_delivered(request,id):
    order = get_object_or_404(OrderItem,id=id)
    if order.payment_option != 'Delivered':
        order.payment_option = 'Delivered'
        order.save()
        return redirect('adminorder')
    
@login_required(login_url='admin')
def adminorder(request):
    orderitem = OrderItem.objects.all()
    user = Customer.objects.all()
    return render(request,'adminpanel/order.html',{'orderitem':orderitem,'user':user})



@login_required(login_url='loginn')
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


@login_required(login_url='loginn')
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


@login_required(login_url='admin')
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


@login_required(login_url='admin')
def salesreport(request):
    products = OrderItem.objects.all()

    context = {
        'products':products
    }

    return render(request,'salesreport.html',context)
    
@login_required(login_url='admin')
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

@login_required(login_url='admin')
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

@login_required(login_url='admin')
def productofferview(request):
    prodoffer = ProductOffer.objects.all()
    return render(request,'productofferview.html',{'prodoffer':prodoffer})

@login_required(login_url='loginn')
def search_products(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query)
    return render(request,'search_results.html',{'product':products})

def refferalcode(request):
    if request.method == 'POST':
        code = request.POST['code']
        category_name = request.POST.get('category')

        try:
            user = Customer.objects.get(first_name=category_name)
            offer = Refferalcode.objects.create(code=code, user=user)
            offer.save()
            
            return redirect('adminpanel') 
        except Product.DoesNotExist:
            pass

    user = Customer.objects.all()
    return render(request,'refferalcode.html',{'user':user})

@login_required(login_url='admin')
def refferalview(request):
    refferal = Refferalcode.objects.all()
    return render(request,'refferalcodeview.html',{'refferal':refferal})


def downloadinvoice(request):
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
    

    return render(request, 'downloadinvoice.html', {
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


def wallet(request):
    if request.user.is_authenticated:
        user = request.user
        cus = Customer.objects.get(email=user)

    return render(request, 'wallet.html', {'user': cus})


def min_price_template_view(request):
    if request.user.is_authenticated: 
        user = request.user
        prod = Product.objects.filter(status =True).order_by('base_price')
        return render(request, 'max_price_template.html', {'addprod' : prod,'usr':user})

def max_price_template_view(request):
    if request.user.is_authenticated: 
        user = request.user
        prod = Product.objects.filter(status =True).order_by('-base_price')
        return render(request, 'max_price_template.html', {'addprod' : prod,'usr':user})
    

def filterby(request):
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    filtered_products = Product.objects.filter(base_price__gte=min_price, base_price__lte=max_price)

    context = {
        'products': filtered_products,
    }

    return render(request, 'categoryfilter.html', context)



@login_required(login_url='admin')
def order_rejected(request, id):
    order_item = get_object_or_404(OrderItem, id=id)
    order = order_item.order
    user = order.user
    customer = Customer.objects.get(email=user.email)

    if order_item.payment_option == 'pending':
        order_item.payment_option = 'Rejected'
        order_item.save()

    if order_item.payment_option == 'Rejected':
        order_item.is_cancel = True
        order_item.save()

        product = order_item.product
        print(product.quantity)
        print(order_item.quantity)

        product.quantity += order_item.quantity
        product.save()

        if order_item.is_paid:
            amount = order_item.item_price
            customer.wallet += float(amount)
            customer.save()

            order_item.item_price = 0
            order_item.save()

        messages.success(request, 'Order item rejected successfully.')
        return redirect('adminorder')

    # Handle the case where the order item is not pending
    messages.warning(request, 'Cannot reject order item. It is not pending.')
    return render(request, 'order.html')



def adminlogout(request):
    auth.logout(request)
    request.session.flush()
    return redirect('loginn')




