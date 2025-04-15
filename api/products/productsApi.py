from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from marshmallow import ValidationError
from .schema import ProductSchema, ReviewSchema
from api.mongoDb import get_collection
import json
from bson import ObjectId
from types import SimpleNamespace
from datetime import datetime
from ..utils.date_utils import validate_and_convert_dates

# Fetch the collection dynamically
product_collection = get_collection("products")
reviews_collection = get_collection("reviews")
product_schema = ProductSchema()
review_schema = ReviewSchema()

@csrf_exempt
def get_products(request):
    """Fetch products with optional filtering and sorting."""
    if request.method == "GET":
        try:
            # Handle query parameters for filtering/sorting
            query = {}
            category = request.GET.get("category")
            if category:
                query["category"] = category

            sort_by = request.GET.get("sort_by", "name")
            order = 1 if request.GET.get("order", "asc") == "asc" else -1

            # Retrieve filtered/sorted products from MongoDB
            products = list(product_collection.find(query).sort(sort_by, order))

            # Convert ObjectId to string for template usage
            for product in products:
                product["_id"] = str(product["_id"])

            # Add a success message
            messages.success(request, f"{len(products)} products fetched successfully.")
            return redirect("render_products")  # Redirect to the products page

        except Exception as e:
            # Add an error message
            messages.error(request, f"Error fetching products: {str(e)}")
            return redirect("render_products")  # Redirect to the products page

    # Add an error message for invalid HTTP methods
    messages.error(request, "Invalid HTTP method.")
    return redirect("render_products")

@csrf_exempt
def get_single_product(request, id):
    try:
        # Fetch the product by its ObjectId
        product = product_collection.find_one({"_id": ObjectId(id)})

        if product:
            product["id"] = str(product["_id"]) 
            product_obj = SimpleNamespace(**product)
            
            context = {
                'product': product_obj,
            }

            return render(request, 'products/product_detail.html', context)
        else:
            messages.error(request, "Product not found")
            return redirect('render_products')
    except Exception as e:
        messages.error(request, f"Error fetching product: {str(e)}")
        return redirect('render_products')

@csrf_exempt
def create_product(request):
    if request.method == "POST":
        try:
            # Check if the request is from a form submission or an API
            if request.content_type == "application/json":
                # Handle JSON-based API request
                data = json.loads(request.body)
            else:
                # Handle form-based submission
                data = {
                    "name": request.POST.get("name"),
                    "description": request.POST.get("description"),
                    "price": float(request.POST.get("price", 0)),
                    "category": request.POST.get("category"),
                    "tags": request.POST.getlist("tags"),
                    "attributes": {
                        "brand": request.POST.get("brand"),
                        "color": request.POST.get("color"),
                        "model": request.POST.get("model"),
                    },
                    "stock": int(request.POST.get("stock", 0)),
                    "seller_id": request.POST.get("seller_id"),
                }

            # Normalize single item or multiple items
            products = [data] if isinstance(data, dict) else data

            valid_products = []
            for product in products:
                try:
                    validated_product = product_schema.load(product)  # Marshmallow validation
                except ValidationError as err:
                    if request.content_type != "application/json":
                        return render(request, "admin/create_product.html", {"error": err.messages})
                    return JsonResponse({"error": err.messages}, status=400)

                # Check for duplicates
                existing_product = product_collection.find_one({
                    "name": {"$regex": f"^{validated_product['name']}$", "$options": "i"},
                    "attributes.brand": {"$regex": f"^{validated_product['attributes']['brand']}$", "$options": "i"},
                    "attributes.color": {"$regex": f"^{validated_product['attributes']['color']}$", "$options": "i"},
                    "attributes.model": {"$regex": f"^{validated_product['attributes']['model']}$", "$options": "i"},
                })

                if existing_product:
                    error_message = f"Product '{validated_product['name']}' with these attributes already exists"
                    if request.content_type != "application/json":
                        return render(request, "admin/create_product.html", {"error": error_message})
                    return JsonResponse({"error": error_message}, status=400)

                valid_products.append(validated_product)

            if not valid_products:
                error_message = "No valid products to insert"
                if request.content_type != "application/json":
                    return render(request, "admin/create_product.html", {"error": error_message})
                return JsonResponse({"error": error_message}, status=400)

            product_collection.insert_many(valid_products)

            success_message = f"{len(valid_products)} Product(s) created successfully"
            if request.content_type != "application/json":
                return render(request, "admin/create_product.html", {"message": success_message})
            return JsonResponse({"message": success_message}, status=201)

        except json.JSONDecodeError:
            error_message = "Invalid JSON"
            if request.content_type != "application/json":
                return render(request, "admin/create_product.html", {"error": error_message})
            return JsonResponse({"error": error_message}, status=400)
        except Exception as e:
            error_message = str(e)
            if request.content_type != "application/json":
                return render(request, "admin/create_product.html", {"error": error_message})
            return JsonResponse({"error": error_message}, status=500)

    elif request.method == "GET":
        # Render the product creation form for GET requests
        return render(request, "admin/create_product.html")

    return JsonResponse({"error": "Method not allowed"}, status=405)
@csrf_exempt
def delete_product(request, product_id):
    if request.method == "DELETE":
        try:
            if not ObjectId.is_valid(product_id):
                messages.error(request, "Invalid product ID format")
                return redirect('render_products')

            # Find the product by ID
            product = product_collection.find_one({"_id": ObjectId(product_id)})

            if not product:
                messages.error(request, "Product not found")
                return redirect('render_products')

            # Delete the product
            result = product_collection.delete_one({"_id": ObjectId(product_id)})

            if result.deleted_count == 0:
                messages.error(request, "Failed to delete product")
                return redirect('render_products')

            messages.success(request, f"Product with ID {product_id} deleted successfully")
            return redirect('render_products')

        except Exception as e:
            messages.error(request, f"Error deleting product: {str(e)}")
            return redirect('render_products')

    messages.error(request, "Method not allowed")
    return redirect('render_products')

@csrf_exempt
def update_product(request, product_id):
    if request.method in ["PUT", "PATCH"]:
        try:
            if not ObjectId.is_valid(product_id):
                error_message = "Invalid product ID format"
                return JsonResponse({"error": error_message}, status=400)

            product = product_collection.find_one({"_id": ObjectId(product_id)})
            if not product:
                error_message = "Product not found"
                return JsonResponse({"error": error_message}, status=404)

            data = json.loads(request.body)
            try:
                validated_data = product_schema.load(data, partial=True)
            except ValidationError as err:
                return JsonResponse({"error": err.messages}, status=400)

            update_result = product_collection.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": validated_data}
            )

            if update_result.matched_count == 0:
                error_message = "No matching product found to update"
                return JsonResponse({"error": error_message}, status=500)

            success_message = f"Product with ID {product_id} updated successfully"
            return JsonResponse({"message": success_message}, status=200)

        except json.JSONDecodeError:
            error_message = "Invalid JSON format"
            return JsonResponse({"error": error_message}, status=400)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({"error": error_message}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def submit_review(request, product_id):
    """Allow customers to submit reviews for a product."""
    if request.method == "POST":
        try:
            # Check if the product exists
            product = product_collection.find_one({"_id": ObjectId(product_id)})
            if not product:
                messages.error(request, "Product not found")
                return redirect("get_single_product", id=product_id)

            # Extract review data from the request
            data = {
                "rating": int(request.POST.get("rating", 0)),
                "review": request.POST.get("review"),
            }

            # Validate the review data
            if not data.get("rating") or not data.get("review"):
                messages.error(request, "All fields (rating, review) are required.")
                return redirect("get_single_product", id=product_id)

            if data["rating"] < 1 or data["rating"] > 5:
                messages.error(request, "Rating must be between 1 and 5.")
                return redirect("get_single_product", id=product_id)

            review = {
                "id": ObjectId(),
                "user_id": request.session.session_key,
                "rating": data["rating"],
                "status": "pending",
                "review": data["review"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            review = validate_and_convert_dates(review, ["created_at", "updated_at", "expires_at"])  # Convert dates to ISO format

            # Validate the review data with ReviewSchema
            try:
                validated_review = review_schema.load(review)  # Validate the review data
            except ValidationError as e:
                messages.error(request, f"Review validation failed: {e.messages}")
                return redirect("get_single_product", id=product_id)
            
            # Append the review to the product's reviews
            reviews_collection.update_one(
                {"product_id": product_id},
                {"$push": {"reviews": validated_review}},
                upsert=True
            )

            messages.success(request, "Review submitted successfully and is pending moderation.")
            return redirect("get_single_product", id=product_id)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect("get_single_product", id=product_id)

    messages.error(request, "Method not allowed")
    return redirect("get_single_product", id=product_id)