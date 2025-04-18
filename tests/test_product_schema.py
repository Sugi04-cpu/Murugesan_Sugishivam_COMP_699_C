import unittest
from datetime import datetime
from bson import ObjectId
from marshmallow.exceptions import ValidationError
from api.products.schema import ProductSchema, IndividualReviewSchema, ReviewSchema


class TestProductSchema(unittest.TestCase):
    def setUp(self):
        self.valid_product_data = {
            "name": "Sample Product",
            "price": 99.99,
            "category": "Electronics",
            "stock": 10,
            "seller_id": str(ObjectId()),
            "discount_percentage": 10,
            "is_active": True,
            "tags": ["electronics", "gadgets"],
            "attributes": {"color": "red", "size": "medium"},
            "image_url": "https://example.com/product.jpg",
            "availability": "In Stock",
        }
    def test_valid_product(self):
        schema = ProductSchema()
        result = schema.load(self.valid_product_data)
        self.assertEqual(result["name"], "Sample Product")
        self.assertEqual(result["price"], 99.99)

    def test_missing_required_field(self):
        schema = ProductSchema()
        invalid_data = self.valid_product_data.copy()
        del invalid_data["name"]  # Missing required field
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)
    def test_invalid_price(self):
        schema = ProductSchema()
        invalid_data = self.valid_product_data.copy()
        invalid_data["price"] = -10.0  # Invalid price
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_stock(self):
        schema = ProductSchema()
        invalid_data = self.valid_product_data.copy()
        invalid_data["stock"] = -5  # Invalid stock
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_discount_percentage(self):
        schema = ProductSchema()
        invalid_data = self.valid_product_data.copy()
        invalid_data["discount_percentage"] = 150  # Invalid discount percentage
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


class TestIndividualReviewSchema(unittest.TestCase):
    def setUp(self):
        self.valid_review_data = {
            "id": str(ObjectId()),
            "user_id": str(ObjectId()),
            "rating": 5,
            "status": "approved",
            "review": "Great product!",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def test_valid_review(self):
        schema = IndividualReviewSchema()
        result = schema.load(self.valid_review_data)
        self.assertEqual(result["rating"], 5)
        self.assertEqual(result["status"], "approved")

    def test_invalid_rating(self):
        schema = IndividualReviewSchema()
        invalid_data = self.valid_review_data.copy()
        invalid_data["rating"] = 6  # Invalid rating
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_status(self):
        schema = IndividualReviewSchema()
        invalid_data = self.valid_review_data.copy()
        invalid_data["status"] = "invalid_status"  # Invalid status
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


class TestReviewSchema(unittest.TestCase):
    def setUp(self):
        self.valid_review_schema_data = {
            "product_id": str(ObjectId()),
            "reviews": [
                {
                    "id": str(ObjectId()),
                    "user_id": str(ObjectId()),
                    "rating": 4,
                    "status": "approved",
                    "review": "Good product.",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ],
        }

    def test_valid_review_schema(self):
        schema = ReviewSchema()
        result = schema.load(self.valid_review_schema_data)
        self.assertEqual(len(result["reviews"]), 1)
        self.assertEqual(result["reviews"][0]["rating"], 4)

    def test_missing_product_id(self):
        schema = ReviewSchema()
        invalid_data = self.valid_review_schema_data.copy()
        del invalid_data["product_id"]  # Missing required field
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_reviews(self):
        schema = ReviewSchema()
        invalid_data = self.valid_review_schema_data.copy()
        invalid_data["reviews"] = []  # Invalid reviews (empty list)
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)