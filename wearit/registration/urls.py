from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.index,name='home'),
    path('products/',views.products,name='products'),
    path('loginn/',views.loginn,name='loginn'),
    path('register/',views.register,name='register'),
    path('productdetails/<int:product_id>/',views.productdetails,name='productdetails'),
    path('adminn/',views.admin,name='admin'),
    path('adminpanel/',views.adminpanel,name='adminpanel'),
    path('productview/',views.productview,name='productview'),
    path('addproduct/',views.addproduct,name='addproduct'),
    path('deleteproduct/<int:id>/',views.deleteproduct,name='deleteproduct'),
    path('adminlogout/',views.adminlogout,name='adminlogout'),
    path('editproduct/<int:id>/',views.editproduct,name='editproduct'),
    path('userview/',views.userview,name='userview'),
    path('offerview/',views.offerview,name='offerview'),
    path('prodoffer/',views.productofferview,name='prodoffer'),
    path('blockuser/<int:id>/',views.blockuser,name='blockuser'),
    path('deletecategory/<int:id>/',views.deletecategory,name='deletecategory'),
    path('otp/',views.otp,name='otp'),
    path('logout', LogoutView.as_view(next_page='home'), name= 'logout'),
    path('addcategory/',views.addcategory,name='addcategory'),
    path('addsize/<int:product_id>/',views.addsize,name='addsize'),
    path('filter/<int:id>/',views.filter,name='filter'),
    path('categoryview/',views.categoryview,name='categoryview'),
    path('editcategory/<int:id>/',views.editcategory,name='editcategory'),
    path('blockcategory/<int:id>/',views.blockcategory,name='blockcategory'),
    path('userprofile/<int:id>/',views.userprofile,name='userprofile'),
    path('addaddress/',views.addaddress,name='addaddress'),
    path('editprofile/',views.editprofile,name='editprofile'),
    path('addressview/',views.addressview,name='addressview'),
    path('addtocart/<int:id>/',views.addtocart,name='addtocart'),
    path('cart/',views.cart,name='cart'),
    path('removefromcart/<int:id>/',views.removefromcart,name='removefromcart'),
    path('checkoutpage/',views.checkoutpage,name='checkoutpage'),
    path('update_quantity/<int:product_id>/', views.update_quantity, name='update_quantity'),
    path('successpage/',views.successpage,name='successpage'),
    path('orderview/',views.orderview,name='orderview'),
    path('cancel_order/<int:id>/',views.cancel_order,name='cancel_order'),
    path('adminorder/',views.adminorder,name='adminorder'),
    path('buynow/<int:id>/',views.buynow,name='buynow'),
    path('return_order/<int:id>/',views.return_order,name='return_order'),
    path('order_delivered/<int:id>/',views.order_delivered,name='order_delivered'),
    path('reviews/<int:id>/',views.reviews,name ='reviews'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path('add_coupon/', views.add_coupon, name='add_coupon'),
    path('venue_pdf/',views.venue_pdf,name='venue_pdf'),
    path('add_offer/',views.add_offer,name='add_offer'),
    path('salesreport/',views.salesreport,name='salesreport'),
    path('searchproduct/',views.search_products,name='search_products'),
    path('refferalcode/',views.refferalcode,name='refferalcode'),
    path('refferalview/',views.refferalview,name='refferalview'),
    
    path('reset_password/',auth_views.PasswordResetView.as_view(template_name="passwordreset.html"),name='reset_password'),

    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name="passwordresetsent.html"),name='password_reset_done'),

    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="passwordresetform.html"),name='password_reset_confirm'),

    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name="passwordresetdone.html"),name='password_reset_complete'),
]
