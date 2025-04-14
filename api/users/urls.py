from django.urls import path
from .usersApi import update_user, delete_user, verify_email, resend_verification
from .address import add_address
from .profileView import profile_view
from .views import edit_user

urlpatterns = [
    path('update/<str:user_id>', update_user, name='update_user'),
    path('edit/<str:user_id>', edit_user, name='edit_user'),
    path("delete/<str:user_id>", delete_user, name="delete_user"),
    path("<str:user_id>/address", add_address, name = "add_address"),
    path('<str:user_id>', profile_view, name='profile_view'),
    path('edit/<str:user_id>/', edit_user, name='edit_user'),
    path('verify-email/<str:token>/<str:user_id>/', verify_email, name='verify_email'),
    path('resend-verification/', resend_verification, name='resend_verification'),
]
