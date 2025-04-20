from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .cart_management_db import (
    get_user_cart,
    create_cart,
    update_cart_item,
    get_cart_items,
    clear_cart
)
from django.core.mail import send_mail
from decouple import config
from bson import ObjectId, errors
import json
from marshmallow import ValidationError
from datetime import datetime, timedelta
from ..mongoDb import get_collection
from .cart_schema import CartSchema
from ..utils.date_utils import validate_and_convert_dates

product_collection = get_collection("products")
carts_collection = get_collection("carts")
user_collection = get_collection("users")
cart_schema = CartSchema()

def handle_response(request, context=None, message=None, status=200, redirect_url=None):
    if status >= 400:
        messages.error(request, message)
    else:
        messages.success(request, message)
    
    if redirect_url:
        return redirect(redirect_url)
    return None

@csrf_exempt
def view_cart(request):
    try:
        cart = get_user_cart(user_id=request.user_data["user_id"]) if request.user_data else get_user_cart(session_id=request.session.session_key)
        if not cart:
            return render(request, 'order_management/cart.html', {
                "cart_items": [], "cart_total": 0, "cart_count": 0,
                "discount_amount": 0, "total_with_discount": 0,
                "remaining_for_free_shipping": 50,
            })

        if not request.user_data:
            if cart.get("expires_at"):
                expires_at = cart["expires_at"]
                current_time = datetime.utcnow()
                if current_time >= expires_at:
                    clear_cart(cart["_id"])
                    messages.warning(request, "Your cart has expired. Items have been cleared.")
                    return render(request, 'order_management/cart.html', {
                        "cart_items": [], "cart_total": 0, "cart_count": 0,
                        "discount_amount": 0, "total_with_discount": 0,
                        "remaining_for_free_shipping": 50,
                    })
                else:
                    hours_remaining = (expires_at - current_time).total_seconds() / 3600
                    if hours_remaining < 4:
                        messages.warning(request, f"Your cart will expire in {int(hours_remaining)} hours.")
                    else:
                        messages.info(request, "Guest carts expire after 24 hours.")

        cart_items = get_cart_items(cart["_id"])
        cart_total = 0
        discount = 0
        for item in cart_items:
            product = item["product"]
            item['product']['id'] = str(product['_id'])
            price = float(product.get("price", 0))
            if product.get("discount"):
                price *= (1 - float(product["discount"]) / 100)
            item["subtotal"] = price * item["quantity"]
            cart_total += item["subtotal"]

        total_with_discount = cart_total
        if cart_total > 100:
            discount = cart_total * 0.1
            total_with_discount -= discount

        context = {
            "cart_items": cart_items,
            "cart_total": round(cart_total, 2),
            "cart_count": len(cart_items),
            "discount_amount": round(discount, 2),
            "total_with_discount": round(total_with_discount, 2),
            "remaining_for_free_shipping": round(max(0, 50 - cart_total), 2),
        }
        return render(request, 'order_management/cart.html', context)

    except Exception as e:
        return handle_response(request, None, f"Error viewing cart: {str(e)}", 500, redirect_url="render_products")

@csrf_exempt
def add_to_cart(request, product_id):
    if request.method != "POST":
        messages.error(request, "Method not allowed.")
        return redirect('view_cart')

    try:
        try:
            product_object_id = ObjectId(product_id)
        except errors.InvalidId:
            return handle_response(request, None, "Invalid product ID.", 400, "view_cart")

        product = product_collection.find_one({"_id": product_object_id})
        if not product:
            return handle_response(request, None, "Product not found.", 404, "view_cart")

        if product.get('stock', 0) <= 0:
            return handle_response(request, None, "Product is out of stock.", 400, "view_cart")

        if request.user_data:
            user_id = request.user_data.get('user_id')
            cart = get_user_cart(user_id=user_id) or create_cart(user_id=user_id) or get_user_cart(user_id=user_id)
        else:
            if not request.session.session_key:
                request.session.create()
            cart = get_user_cart(session_id=request.session.session_key) or create_cart(session_id=request.session.session_key) or get_user_cart(session_id=request.session.session_key)

        if not cart:
            raise Exception("Failed to create or retrieve cart.")

        quantity = 1
        form_quantity = request.POST.get("quantity")
        if form_quantity:
            quantity = int(form_quantity)

        if quantity <= 0:
            return handle_response(request, None, "Quantity must be positive.", 400, "view_cart")
        if quantity > product.get('stock', 0):
            return handle_response(request, None, f"Only {product.get('stock')} items available.", 400, "view_cart")

        cart = validate_and_convert_dates(cart, ["created_at", "updated_at", "expires_at"])

        try:
            cart_schema.load(cart)
        except ValidationError as e:
            return handle_response(request, None, f"Cart validation failed: {e.messages}", 400, "view_cart")

        current_cart_items = get_cart_items(cart["_id"])
        existing_item = next((item for item in current_cart_items if str(item["product"]["_id"]) == product_id), None)

        if existing_item and (existing_item["quantity"] + quantity) > product.get('stock', 0):
            return handle_response(request, None, f"Only {product.get('stock') - existing_item['quantity']} more items available.", 400, "view_cart")

        update_cart_item(str(cart["_id"]), str(product_id), quantity)

        return handle_response(request, None, "Item added to cart successfully.", 200, "view_cart")

    except Exception as e:
        return handle_response(request, None, str(e), 500, "view_cart")

@csrf_exempt
def update_cart(request, product_id):
    if request.method != "POST":
        return handle_response(request, None, "Method not allowed", 405, "view_cart")

    try:
        cart = get_user_cart(user_id=request.user_data["user_id"]) if request.user_data else get_user_cart(session_id=request.session.session_key)
        if not cart:
            return handle_response(request, None, "Cart not found", 404, "view_cart")

        action = request.POST.get("action")
        if action not in ["increase", "decrease", "remove"]:
            return handle_response(request, None, "Invalid action", 400, "view_cart")

        cart_items = get_cart_items(cart["_id"])
        current_item = next((item for item in cart_items if str(item["product"]["_id"]) == product_id), None)
        if not current_item:
            return handle_response(request, None, "Item not found in cart", 404, "view_cart")

        if action == "increase":
            product = product_collection.find_one({"_id": ObjectId(product_id)})
            if current_item["quantity"] >= product.get("stock", 0):
                return handle_response(request, None, "Not enough stock available", 400, "view_cart")
            
            new_quantity = current_item["quantity"] + 1
        elif action == "decrease":
            new_quantity = max(1, current_item["quantity"] - 1)

        else:
            new_quantity = 0

        update_cart_item(str(cart["_id"]), str(product_id), new_quantity, "remove" if action == "remove" else None)

        messages.success(request, "Cart updated successfully")
        return redirect("view_cart")

    except Exception as e:
        return handle_response(request, None, str(e), 500, "view_cart")

@csrf_exempt
def clear_cart_view(request):
    if request.method != "POST":
        return handle_response(request, None, "Method not allowed", 405, "view_cart")

    try:
        cart = get_user_cart(user_id=request.user_data["user_id"]) if request.user_data else get_user_cart(session_id=request.session.session_key)
        if not cart:
            return handle_response(request, None, "Cart not found", 404, "view_cart")

        clear_cart(cart["_id"])
        return handle_response(request, None, "Cart cleared successfully", 200, "view_cart")

    except Exception as e:
        return handle_response(request, None, f"Error clearing cart: {str(e)}", 500, "view_cart")

@csrf_exempt
def remove_from_cart(request, product_id):
    if request.method != "POST":
        return handle_response(request, None, "Method not allowed", 405, "view_cart")

    try:
        cart = get_user_cart(user_id=request.user_data["user_id"]) if request.user_data else get_user_cart(session_id=request.session.session_key)
        if not cart:
            return handle_response(request, None, "Cart not found", 404, "view_cart")

        product_id_str = str(product_id)
        cart_items = get_cart_items(cart["_id"])
        if not any(str(item["product"]["_id"]) == product_id_str for item in cart_items):
            return handle_response(request, None, "Item not found in cart", 404, "view_cart")

        update_cart_item(str(cart["_id"]), product_id_str, 0, "remove")
        return handle_response(request, None, "Item removed from cart successfully", 200, "view_cart")

    except Exception as e:
        return handle_response(request, None, f"Error removing item from cart: {str(e)}", 500, "view_cart")
