from django.shortcuts import render,redirect,HttpResponse,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,MyAccountManager,UserProfile
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required
#ACTIVATION IMPORTS
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_text
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id
from carts.models import Cart,CartItem
import requests
from orders.models import Order
# Create your views here.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password,username=username)
            user.phone = phone
            user.save()
            #USER ACTIVATION
            current_site = get_current_site(request)
            mail_subject = 'Please Activate Your Account'
            message = render_to_string('accounts/account_verification_mail.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            #messages.success(request,'Thankyou for registration Please verify your email to proceed')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    context = {
        'form':form,
    }
    return render(request,"accounts/register.html",context)

def activate(request,uidb64,token):
    User = auth.get_user_model()
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request,'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        messages.error(request,'Activation link is invalid!')
        return redirect('register')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(request,email=email,password=password)
        if user is not None:
            try:
                cart = Cart.objects.get(card_id = _cart_id(request))
                is_cart_item_exist = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exist:
                    cart_item = CartItem.objects.filter(cart=cart)
                    #getting product variation from cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    #get the cart item from user
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id  = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request,user)
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextpage = params['next']
                    return redirect(nextpage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request,'Invalid credentials')
            return redirect('login')
    return render(request,'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request,'You are logged out')
    return redirect('login')

@login_required(login_url = 'login')
def dashboard(request):
    order = Order.objects.filter(user_id=request.user.id,is_ordered=True).order_by('-created_at')
    order_quantity = order.count()
    context = {
        'order_quantity':order_quantity
    }
    return render(request,'accounts/dashboard.html',context)

def forgetpassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            #Forget Password Email verificationcurrent
            current_site = get_current_site(request)
            mail_subject = 'Reset Password'
            message = render_to_string('accounts/reset_password_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            messages.success(request, 'Password reset link has been send to your email')
            return redirect('login')

        else:
            messages.error(request,'Account does not exits')
            return redirect('forgetpassword')
    return render(request,'accounts/forgetpassword.html')

def reset_password_validate(request,uidb64,token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request,'Please reset your password')
        return redirect('resetpassword')
    else:
        messages.error(request,"this link has been expired")
        return redirect('login')


def resetpassword(request):
    if request.method == 'POST':
        password = request.POST["password"]
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password changes successfully')
            return redirect('login')

        else:
            messages.error(request,'Password do not match')
            return redirect('resetpassword')
    return render(request,'accounts/resetpassword.html')

def my_orders(request):
    orders = Order.objects.filter(user_id=request.user.id,is_ordered=True).order_by('-created_at')
    context = {
        'orders':orders,
    }
    return render(request,'accounts/my_orders.html',context)

def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        userform = UserForm(request.POST,instance=request.user)
        profileform = UserProfileForm(request.POST,request.FILES,instance=request.user)
        if userform.is_valid() and profileform.is_valid():
            userform.save()
            profileform.save()
            messages.success(request,"Your profile has been updated")
            return redirect('edit_profile')
    else:
        userform = UserForm(instance=request.user)
        profileform = UserProfileForm(instance=userprofile)
    context = {
        'userform':userform,
        'profileform':profileform,
        'userprofile':userprofile
    }
    return render(request,'accounts/edit_profile.html',context)
