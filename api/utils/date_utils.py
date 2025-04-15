from datetime import datetime

def validate_and_convert_dates(data, fields):
    """
    Ensure that all specified datetime fields in the data are valid and properly formatted.
    
    Args:
        data (dict): The dictionary containing the fields to validate.
        fields (list): A list of field names to validate and convert.

    Returns:
        dict: The updated dictionary with properly formatted datetime fields.
    """
    for field in fields:
        if field in data:
            if isinstance(data[field], str):
                # Convert ISO 8601 string to datetime object
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError:
                    raise ValueError(f"Invalid datetime format for field '{field}': {data[field]}")
            elif not isinstance(data[field], datetime):
                raise ValueError(f"Field '{field}' must be a datetime object or ISO 8601 string.")
    return data