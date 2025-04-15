import unittest
from datetime import datetime
from bson import ObjectId
from marshmallow.exceptions import ValidationError
from api.users.userSchema import UserSchema, AddressSchema


class TestAddressSchema(unittest.TestCase):
    def setUp(self):
        self.valid_address_data = {
            "user_id": str(ObjectId()),
            "type": "home",
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
            "country": "USA",
            "phone": "123-456-7890",
        }

    def test_valid_address(self):
        schema = AddressSchema()
        result = schema.load(self.valid_address_data)
        self.assertEqual(result["type"], "home")
        self.assertEqual(result["city"], "New York")

    def test_missing_required_field(self):
        schema = AddressSchema()
        invalid_data = self.valid_address_data.copy()
        del invalid_data["street"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_user_id(self):
        schema = AddressSchema()
        invalid_data = self.valid_address_data.copy()
        invalid_data["user_id"] = "invalid_object_id"
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)


class TestUserSchema(unittest.TestCase):
    def setUp(self):
        self.valid_user_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123",
            "role": "customer",
            "is_active": True,
            "is_locked": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "addresses": [
                {
                    "user_id": str(ObjectId()),
                    "type": "home",
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001",
                    "country": "USA",
                }
            ],
            "permissions": {"can_edit": True, "can_delete": False},
            "failed_attempts": 0,
            "last_failed_attempt": datetime.utcnow().isoformat(),
        }

    def test_valid_user(self):
        schema = UserSchema()
        result = schema.load(self.valid_user_data)
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["role"], "customer")
        self.assertTrue(result["is_active"])

    def test_missing_required_field(self):
        schema = UserSchema()
        invalid_data = self.valid_user_data.copy()
        del invalid_data["email"]
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_email(self):
        schema = UserSchema()
        invalid_data = self.valid_user_data.copy()
        invalid_data["email"] = "invalid-email"
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_invalid_role(self):
        schema = UserSchema(context={"is_admin": False})
        invalid_data = self.valid_user_data.copy()
        invalid_data["role"] = "admin"
        with self.assertRaises(ValidationError):
            schema.load(invalid_data)

    def test_default_values(self):
        schema = UserSchema()
        data = {
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "password": "securepassword123",
        }
        result = schema.load(data)
        self.assertEqual(result["role"], "customer")
        self.assertTrue(result["is_active"])
        self.assertFalse(result["is_locked"])
        self.assertEqual(result["failed_attempts"], 0)