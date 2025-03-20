from marshmallow import Schema, fields, ValidationError, validate
from bson import ObjectId
import datetime
from api.mongoDb import get_collection



# Custom field for ObjectId validation
class ObjectIdField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, ObjectId):
            raise ValidationError("Invalid ObjectId")
        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return ObjectId(value)
        except Exception:
            raise ValidationError("Invalid ObjectId")


# Define Product Schema dynamically
ProductSchema = Schema.from_dict({
    "_id": ObjectIdField(required=False, allow_none=True),
    "name": fields.Str(required=True),
    "price": fields.Float(required=True, validate=lambda x: x >= 0),  # Price must be >= 0
    "category": fields.Str(required=True),
    "stock": fields.Int(required=True, validate=lambda x: x >= 0),  # Stock must be >= 0
    "seller_id": fields.Raw(required=True, allow_none=True),
    "is_popular": fields.Bool(required=False, default=False),               # Popular product flag
    "low_stock_threshold": fields.Int(required=False, default=10),          # Alert when stock < 10
    "discount_percentage": fields.Int(required=False, default=0, validate=validate.Range(min=0, max=100)),
    "is_active": fields.Bool(required=False, default=True),                 # Hide inactive products
    "tags": fields.List(fields.Str(), required=False),                      # Tags for filtering
    "created_at": fields.DateTime(required=False, dump_default=datetime.datetime.now()),
    "updated_at": fields.DateTime(required=False, dump_default=datetime.datetime.now()),
    "attributes": fields.Dict(
        required=True,
        keys=fields.Str(),
        values=fields.Raw(),
        description="A flexible dictionary for product-specific attributes"
    ),
    "image_url": fields.Url(),
    "availability": fields.Str(required=False, default=True),
})


