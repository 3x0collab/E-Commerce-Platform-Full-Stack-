from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import datetime
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import contact_us
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import copy

# local imports
from .models import *
from .utils import cartData

# Shop Home
def home(request):
    
    data = cartData(request)

    products = Product.objects.all() # all the products
    for x in products:
        if x.product_image2:
            print("name",x.name, x.product_image2)
    cartItems = data['cartItems'] # cart item count
    items = data['items'] # Items in Cart
    
    context = {
        'products': products,
        'cartItems': cartItems,
        'items': items,
    }
    return render(request, 'shop/index.html', context=context)

# Shop About :- /tss/about
def about(request):
    return render(request, 'shop/about.html')

# Shop About :- /tss/about
def direct_payment(request,cartid):
    return render(request, 'shop/direct_payment.html')


@csrf_exempt
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Send the email
        email_subject = f'New Contact Form Submission - Form F and F venture Customer'
        email_message = f'Name: {name}\nEmail: {email}\nMessage: {message}'
        from_email = '3xotech@gmail.com'
        to_email = ['fandfglobal1@gmail.com']  # Replace with the recipient's email
        send_mail(email_subject, email_message, from_email, to_email, fail_silently=False)

        # Return a success message
        response_data = {'status': 'success', 'message': 'Message sent successfully'}
        return JsonResponse(response_data)
    
    return render(request, 'shop/contact-us.html')


# Shop ContactUs:- /tss/contact
def preview(request,preview):
    data = cartData(request)
    cartItems = data['cartItems'] # cart item count

    product = Product.objects.get(pk=preview) # all the products
    context = {
    'product': product,
    "cartItems":cartItems
    }
    return render(request, 'shop/preview.html', context=context) 
# 'template':product.product_image2.url,
#     'price':product.price,
#     'name':product.name,
#     'description':product.description,
def deletecart(request,cartid):
    cart = OrderItem.objects.get(pk=cartid).delete() # all the products
    return HttpResponseRedirect(reverse('cart'))

# Shop Items :- /shop
def shop(request):
    category = request.GET.get('category')
    q = request.GET.get('q')

    if q:
        products = Product.objects.filter(name__icontains=q)
    else:
        products = Product.objects.all() 

    if category:
        products = products.filter(category__iexact=category) 

    side_menu = Product.objects.all().values("category").annotate(count=Count("category")) 
    menus={}
    for sm in side_menu:
        if not menus.get(sm["category"]):
            menus[sm["category"]] = sm
        else:
            # print('sdhhshghsdghhgsdgh')
            menus[sm["category"]]['count']+=1

    for ch in CHOICES:
        if not menus.get(ch[0]):
            menus[ch[0]] = {'category':ch[0],'count':0}

    menus = list(menus.values())
    menus.sort(key=lambda x:x['count'],reverse=True)
    data = cartData(request)
    cartItems = data['cartItems']
    items = data['items'] # Items in Cart
    
    context = {
        'products': products,
        'cartItems': cartItems,
        'items': items,
        'menus': menus,
        'q': q,
    }
    return render(request, 'shop/shop.html', context=context)

# Item Cart :- tss/cart/
def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {
        'items': items, # items in the cart
        'order': order, # order object for the customer
        'cartItems': cartItems, # cart item count
        'shipping':False, # shiiping boolean value to ask for address or not
    }
    print(context)
    return render(request, 'shop/cart.html', context=context)

@login_required
# Checkout tss/checkout
def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    if request.user.is_authenticated:
        name = ", ".join([ item['product']['name'] for item in items])
    else:
        name = ", ".join([ item.product.name for item in items])

    context = {
        'items': items,   # items in the cart 
        'order': order,   # order object for the customer
        'cartItems': cartItems,  # cart item count
        'shipping':False,   # shiiping boolean value to ask for address or not,
        'name':name
    }
    return render(request, 'shop/checkout.html', context=context)

# Item Detail
# def itemDetail(request):
#     return render(request, 'shop/item-detail.html')

# To update Items in the cart of the customer
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action: ', action)
    print('Product: ', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete = False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    orderItem.quantity+= 1 if action == 'add' else -1
    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()
    
    return JsonResponse('Item was added', safe=False)

# Function to process Order
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    print(data)

    if request.user.is_authenticated:
        # Creating Customer
        customer = request.user.customer
        customer.fname = data['user']['firstName']
        customer.lname = data['user']['lastName']
        customer.email = data['user']['email']

        order, created = Order.objects.get_or_create(customer=customer, complete = False)
        total = float(data['user']['total'])
        order.transaction_id = transaction_id

        if total == order.get_cart_total:
            order.complete = True

        order.save()

        if order.shipping == True:
            ShippingAdress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address']+' '+data['shipping']['address2'],
                city=data['shipping']['country'],
                state=data['shipping']['state'],
                zipcode=data['shipping']['zip'],
            )
    else:
        return redirect('login')

    name = '{} {}'.format(data['user'].get("firstName"), data['user'].get("lastName"))

    text = f"""
    Hi,
    My name is {name}, \n
    I ordered from fandfglobal.ng,  \n

    Transaction ID: {transaction_id}, \n
    Goods: {data['user'].get('name')},\n
    Email: {data['user']['email']},\n
    Price: {data['user']['total']},\n
    Shipping Location: {", ".join([ f'{key}:{data.get("shipping").get(key)}' for key in data.get("shipping") if data.get("shipping").get(key)  ])}
    """

    whatsapp_msg = f"https://api.whatsapp.com/send?phone=+234-8153839345&text={text}:%20[See Payment Screenshot Below]"
    email_message = f"mailto:fandfglobal1@gmail.com?subject=Goods%20Order%20From%20{name}&body={text}"

    return render(request, 'shop/direct_payment.html', {"whatsapp_msg":whatsapp_msg,'email_message':email_message} )


# To update Items in the cart of the customer
def formprocess(request):
    data = request.POST
    name = data.get('name')
    datacopy = copy.copy(data)
    if datacopy.get("csrfmiddlewaretoken"):
        del datacopy['csrfmiddlewaretoken']
    contact_us.objects.create(**datacopy)

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Send the email
        email_subject = f'New Contact Form Submission - Form F and F venture Customer'
        email_message = f'Name: {name}\nEmail: {email}\nMessage: {message}'
        from_email = '3xotech@gmail.com'
        to_email = ['fandfglobal1@gmail.com']  # Replace with the recipient's email
        send_mail(email_subject, email_message, from_email, to_email, fail_silently=False)
    
    return JsonResponse('Your message have sent, Get back to u shortly', safe=False)

