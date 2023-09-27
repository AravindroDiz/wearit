from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

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

]
