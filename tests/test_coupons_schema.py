import unittest
from datetime import datetime, timedelta
from marshmallow.exceptions import ValidationError
from api.cart_management.cart_schema import CouponSchema


class TestCouponSchema(unittest.TestCase):
    def setUp(self):
        self.valid_coupon_data = {
            "code": "DISCOUNT10",
            "discount": 10.0,
            "expiry_date": (datetime.utcnow() + timedelta(days=10)),
            "max_uses": 5,
            "used_count": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        self.valid_coupon_data["expiry_date"] = self.valid_coupon_data["expiry_date"].isoformat()
        self.valid_coupon_data["created_at"] = self.valid_coupon_data["created_at"].isoformat()
        self.valid_coupon_data["updated_at"] = self.valid_coupon_data["updated_at"].isoformat()

    def test_valid_coupon(self):
        schema = CouponSchema()
        result = schema.load(self.valid_coupon_data)
        self.assertEqual(result["code"], "DISCOUNT10")
        self.assertEqual(result["discount"], 10.0)

    def test_missing_code(self):
        schema = CouponSchema()
        invalid_data = self.valid_coupon_data.copy()
        del invalid_data["code"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_discount(self):
        schema = CouponSchema()
        invalid_data = self.valid_coupon_data.copy()
        invalid_data["discount"] = -5.0
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_expired_coupon(self):
        schema = CouponSchema()
        invalid_data = self.valid_coupon_data.copy()
        # Convert to ISO string before passing
        invalid_data["expiry_date"] = (datetime.utcnow() - timedelta(days=10)).isoformat()
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


    def test_default_values(self):
        schema = CouponSchema()
        data = {
            "code": "DISCOUNT10",
            "discount": 10.0,
            "expiry_date": (datetime.utcnow() + timedelta(days=10)).isoformat()  # Add .isoformat()
        }
        result = schema.load(data)
        self.assertEqual(result["used_count"], 0)
        self.assertTrue(result["is_active"])