from django.http import JsonResponse
from django.shortcuts import render
from marshmallow import ValidationError
from .schema import ProductSchema
from api.mongoDb import get_collection
import json
from bson import ObjectId
from types import SimpleNamespace

# Fetch the collection dynamically
product_collection = get_collection("products")
product_schema = ProductSchema()

def get_products(request):
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
            
            # Convert ObjectId to string for JSON serialization
            for product in products:
                product["_id"] = str(product["_id"])  # Convert ObjectId to string
            
            return JsonResponse(products, safe=False, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

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

            print(context)

            return render(request, 'productDetail.html', context)
        else:
            return JsonResponse({"error": "Product not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
