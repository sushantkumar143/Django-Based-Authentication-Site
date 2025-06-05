from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class OTPVerification(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def generate_otp(self):
        self.otp = ''.join(random.choices(string.digits, k=6))
        return self.otp
    
    def is_expired(self):
        expiry_time = self.created_at + timezone.timedelta(minutes=2)
        return timezone.now() > expiry_time
    
    def __str__(self):
        return f"OTP for {self.email}"

class BMIRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    height = models.FloatField()  # in cm
    weight = models.FloatField()  # in kg
    bmi = models.FloatField()
    category = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_bmi(self):
        height_m = self.height / 100
        self.bmi = round(self.weight / (height_m ** 2), 2)
        
        if self.bmi < 18.5:
            self.category = 'Underweight'
        elif 18.5 <= self.bmi < 25:
            self.category = 'Normal'
        elif 25 <= self.bmi < 30:
            self.category = 'Overweight'
        else:
            self.category = 'Obese'
    
    def __str__(self):
        return f"{self.user.username} - BMI: {self.bmi}"
