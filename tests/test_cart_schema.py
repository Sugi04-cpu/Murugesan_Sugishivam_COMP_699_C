import unittest
from datetime import datetime, timedelta
from bson import ObjectId
from marshmallow.exceptions import ValidationError
from api.cart_management.cart_schema import CartSchema, CouponSchema

class TestCartSchema(unittest.TestCase):
    def setUp(self):
        self.valid_cart_data = {
            "session_id": "session123",
            "user_id": str(ObjectId()),
            "items": [{"product_id": str(ObjectId()), "quantity": 2}],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        }

    def test_valid_cart(self):
        schema = CartSchema()
        result = schema.load(self.valid_cart_data)
        self.assertEqual(result["session_id"], "session123")
        self.assertEqual(len(result["items"]), 1)

    def test_missing_session_id(self):
        schema = CartSchema()
        invalid_data = self.valid_cart_data.copy()
        del invalid_data["session_id"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_user_id(self):
        schema = CartSchema()
        invalid_data = self.valid_cart_data.copy()
        invalid_data["user_id"] = "invalid_object_id"
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_default_values(self):
        schema = CartSchema()
        data = {
            "session_id": "session123",
        }
        result = schema.load(data)
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
        self.assertIn("expires_at", result)


