from django.shortcuts import render
from bson import ObjectId
from ..mongoDb import get_collection

users_collection = get_collection("users")

def edit_user(request, user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return render(request, "error.html", {"error": "User not found"})
        # Transform the ObjectId field
        user['id'] = str(user.get('_id'))
        return render(request, "users/edit_user.html", {
            "user": user,
            "admin_name": request.user_data.get('email')
        })
    except Exception as e:
        return render(request, "error.html", {"error": str(e)})