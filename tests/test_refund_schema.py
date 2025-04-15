import unittest
from datetime import datetime
from bson import ObjectId
from marshmallow.exceptions import ValidationError
from api.orders.order_schema import RefundRequestSchema, OrderItemSchema


class TestRefundRequestSchema(unittest.TestCase):
    def setUp(self):
        self.valid_refund_request_data = {
            "order_id": str(ObjectId()),
            "user_id": str(ObjectId()),
            "reason": "Defective product",
            "status": "Pending",
            "requested_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def test_valid_refund_request(self):
        schema = RefundRequestSchema()
        result = schema.load(self.valid_refund_request_data)
        self.assertEqual(result["reason"], "Defective product")
        self.assertEqual(result["status"], "Pending")

    def test_invalid_status(self):
        schema = RefundRequestSchema()
        invalid_data = self.valid_refund_request_data.copy()
        invalid_data["status"] = "InvalidStatus"  # Invalid status
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_missing_order_id(self):
        schema = RefundRequestSchema()
        invalid_data = self.valid_refund_request_data.copy()
        del invalid_data["order_id"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_missing_reason(self):
        schema = RefundRequestSchema()
        invalid_data = self.valid_refund_request_data.copy()
        del invalid_data["reason"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)