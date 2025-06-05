from django.contrib import admin
from .models import UserProfile, OTPVerification, BMIRecord

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'gender', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'otp', 'created_at', 'is_verified']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email']

@admin.register(BMIRecord)
class BMIRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'bmi', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__username']