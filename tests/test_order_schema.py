import unittest
from datetime import datetime
from bson import ObjectId
from marshmallow.exceptions import ValidationError
from api.orders.order_schema import OrderSchema, RefundRequestSchema, OrderItemSchema


class TestOrderItemSchema(unittest.TestCase):
    def setUp(self):
        self.valid_order_item_data = {
            "product_id": str(ObjectId()),
            "quantity": 2,
            "price": 50.0,
        }

    def test_valid_order_item(self):
        schema = OrderItemSchema()
        result = schema.load(self.valid_order_item_data)
        self.assertEqual(result["quantity"], 2)
        self.assertEqual(result["price"], 50.0)

    def test_invalid_quantity(self):
        schema = OrderItemSchema()
        invalid_data = self.valid_order_item_data.copy()
        invalid_data["quantity"] = 0  # Invalid quantity
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_missing_product_id(self):
        schema = OrderItemSchema()
        invalid_data = self.valid_order_item_data.copy()
        del invalid_data["product_id"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


class TestOrderSchema(unittest.TestCase):
    def setUp(self):
        self.valid_order_data = {
            "user_id": str(ObjectId()),
            "items": [
                {
                    "product_id": str(ObjectId()),
                    "quantity": 2,
                    "price": 50.0,
                }
            ],
            "total_price": 100.0,
            "status": "Pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def test_valid_order(self):
        schema = OrderSchema()
        result = schema.load(self.valid_order_data)
        self.assertEqual(result["status"], "Pending")
        self.assertEqual(result["total_price"], 100.0)

    def test_invalid_total_price(self):
        schema = OrderSchema()
        invalid_data = self.valid_order_data.copy()
        invalid_data["total_price"] = -10.0  # Invalid total price
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_status(self):
        schema = OrderSchema()
        invalid_data = self.valid_order_data.copy()
        invalid_data["status"] = "InvalidStatus"  # Invalid status
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_missing_user_id(self):
        schema = OrderSchema()
        invalid_data = self.valid_order_data.copy()
        del invalid_data["user_id"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


