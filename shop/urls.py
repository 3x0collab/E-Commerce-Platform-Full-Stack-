from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tss/about/', views.about, name='about'),
    path('direct_payment/<int:cartid>/', views.direct_payment, name='direct_payment'),
    path('tss/contact-us/', views.contact, name='contact-us'),
    path('tss/contact-us/form-process', views.formprocess, name='formprocess'),
    path('tss/preview/<int:preview>/', views.preview, name='preview'),
    path('shop/', views.shop, name='shop'),  
    path('tss/cart/', views.cart, name='cart'),  
    path('tss/cart/<int:cartid>/', views.deletecart, name='deletecart'),
    path('tss/checkout/', views.checkout, name='checkout'),
    path('process_order/', views.processOrder, name='process_order'),
    path('update/', views.updateItem, name='update'),
]