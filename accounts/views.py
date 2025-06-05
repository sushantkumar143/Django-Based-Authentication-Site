from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from .models import UserProfile, OTPVerification, BMIRecord
from .forms import CustomUserCreationForm, BMIForm, ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
import json

def dashboard(request):
    return render(request, 'dashboard.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')  # This checks if the user was trying to visit a protected page before login.
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def user_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('dashboard')

@login_required
def bmi_calculator(request):
    if request.method == 'POST':
        form = BMIForm(request.POST)
        if form.is_valid():
            bmi_record = form.save(commit=False)
            bmi_record.user = request.user
            bmi_record.calculate_bmi()
            bmi_record.save()
            
            context = {
                'form': BMIForm(),
                'bmi_result': bmi_record,
                'show_result': True
            }
            return render(request, 'bmi_calculator.html', context)
    else:
        form = BMIForm()
    
    return render(request, 'bmi_calculator.html', {'form': form})

@login_required
def summary(request):
    bmi_records = BMIRecord.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'bmi_records': bmi_records,
        'total_records': bmi_records.count()
    }
    return render(request, 'summary.html', context)

def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Delete existing OTP for this email
                OTPVerification.objects.filter(email=email).delete()
                
                # Create new OTP
                otp_obj = OTPVerification(email=email)
                otp = otp_obj.generate_otp()
                otp_obj.save()
                
                # Send OTP via email
                subject = 'Password Reset OTP'
                message = f'Your OTP for password reset is: {otp}\nThis OTP will expire in 2 minutes.'
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                request.session['reset_email'] = email
                messages.success(request, 'OTP sent to your email address.')
                return redirect('verify_otp')
                
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'forgot_password.html', {'form': form})

def verify_otp(request):
    if 'reset_email' not in request.session:
        return redirect('forgot_password')
    
    email = request.session['reset_email']
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            try:
                otp_obj = OTPVerification.objects.get(email=email, otp=entered_otp, is_verified=False)
                
                if otp_obj.is_expired():
                    messages.error(request, 'OTP has expired. Please request a new one.')
                    return redirect('forgot_password')
                
                otp_obj.is_verified = True
                otp_obj.save()
                
                request.session['otp_verified'] = True
                return redirect('reset_password')
                
            except OTPVerification.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    # Check if OTP exists and get remaining time
    try:
        otp_obj = OTPVerification.objects.get(email=email, is_verified=False)
        created_time = otp_obj.created_at.timestamp()
        current_time = timezone.now().timestamp()
        remaining_time = max(0, 120 - (current_time - created_time))  # 2 minutes = 120 seconds
    except OTPVerification.DoesNotExist:
        return redirect('forgot_password')
    
    context = {
        'form': form,
        'email': email,
        'remaining_time': int(remaining_time)
    }
    return render(request, 'verify_otp.html', context)

def reset_password(request):
    if 'reset_email' not in request.session or not request.session.get('otp_verified'):
        return redirect('forgot_password')
    
    email = request.session['reset_email']
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Clean up session and OTP
                del request.session['reset_email']
                del request.session['otp_verified']
                OTPVerification.objects.filter(email=email).delete()
                
                messages.success(request, 'Password reset successful! You can now login with your new password.')
                return redirect('login')
                
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'reset_password.html', {'form': form})
