from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from api.mongoDb import get_collection
from .userSchema import UserSchema
from django.contrib.auth.hashers import make_password
import json
import jwt
from decouple import config
from datetime import datetime
from marshmallow import ValidationError
from bson import ObjectId

users_collection = get_collection("users")

def is_json_request(request):
    return request.content_type == "application/json"

def get_users(request):
    """Admin API to get all users using token stored in cookies under 'auth_token'"""
    token = request.COOKIES.get("auth_token").split(" ")[1]
    if not token:
        if is_json_request(request):
            return JsonResponse({"error": "Authorization token required"}, status=401)
        else:
            messages.error(request, "Authorization token required")
            return redirect("render_products")
    try:
        # Decode the JWT token from cookies
        decoded_token = jwt.decode(token, config("SECRET_KEY"), algorithms=["HS256"])
        # Check if the role is admin
        if decoded_token.get("role") != "admin":
            if is_json_request(request):
                return JsonResponse({"error": "Access denied, admin role required"}, status=403)
            else:
                messages.error(request, "Access denied, admin role required")
                return redirect("render_products")
        # Fetch all users if admin role
        users = list(users_collection.find())
        # Remove sensitive information before returning
        for user in users:
            user["_id"] = str(user["_id"])
            if "password" in user:
                del user["password"]

        if is_json_request(request):
            return JsonResponse({"users": users}, status=200)
        else:
            messages.success(request, "Users retrieved successfully")
            return redirect("render_products")

    except jwt.ExpiredSignatureError:
        error_msg = "Token has expired"
    except jwt.InvalidTokenError:
        error_msg = "Invalid token"
    except Exception as e:
        error_msg = str(e)

    if is_json_request(request):
        return JsonResponse({"error": error_msg}, status=401)
    else:
        messages.error(request, error_msg)
        return redirect("render_products")




