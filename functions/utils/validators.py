"""Data validation utility functions."""
import re
from typing import Dict, Any, List


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    # More strict email pattern
    email_pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: The phone number to validate

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
        
    # Allow different formats: (123) 456-7890, 123-456-7890, 123.456.7890, etc.
    phone_pattern = r'^(\+\d{1,3}\s?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}$'
    return bool(re.match(phone_pattern, phone))


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate that all required fields are present and not empty.

    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that are required

    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "missing_fields": []
    }

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            result["valid"] = False
            result["missing_fields"].append(field)

    return result


def sanitize_input(text: str) -> str:
    """
    Sanitize input text to prevent injection attacks.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text
    """
    if text is None:
        return None
    
    if not text:
        return ""
    
    # Define safe tags to keep
    safe_tags = ['b', 'i', 'u', 'em', 'strong']
    
    # Remove potentially dangerous HTML/script tags but keep safe ones
    sanitized = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Only remove tags that aren't in our safe list
    for tag in safe_tags:
        # Temporarily replace safe tags with markers
        sanitized = re.sub(f'<{tag}>(.*?)</{tag}>', f'__SAFE_TAG_{tag}_START__\\1__SAFE_TAG_{tag}_END__', 
                          sanitized, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    sanitized = re.sub(r'<.*?>', '', sanitized)
    
    # Restore safe tags
    for tag in safe_tags:
        sanitized = re.sub(f'__SAFE_TAG_{tag}_START__(.*?)__SAFE_TAG_{tag}_END__', 
                          f'<{tag}>\\1</{tag}>', sanitized)
    
    # Limit the length to prevent overflow attacks
    if len(sanitized) > 5000:
        sanitized = sanitized[:5000]
    
    return sanitized.strip()


def validate_object(
    data: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]],
    partial: bool = False
) -> Dict[str, Any]:
    """
    Validate object against a schema.

    Args:
        data: Dictionary containing the data to validate
        schema: Dictionary defining the schema (fields, types, validation)
        partial: If True, only validates fields that are present in data

    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "errors": {}
    }

    # Check required fields if not partial validation
    if not partial:
        required_fields = [field for field, props in schema.items() if props.get("required", False)]
        required_check = validate_required_fields(data, required_fields)

        if not required_check["valid"]:
            result["valid"] = False
            for field in required_check["missing_fields"]:
                result["errors"][field] = f"Field '{field}' is required"

    # Validate fields that are present
    for field_name, field_value in data.items():
        # Skip fields not in schema
        if field_name not in schema:
            continue

        field_schema = schema[field_name]
        field_type = field_schema.get("type")

        # Type validation
        if field_type and not isinstance(field_value, field_type):
            result["valid"] = False
            result["errors"][field_name] = (
                f"Expected type {field_type.__name__}, got {type(field_value).__name__}"
            )
            continue

        # Custom validation function
        validator = field_schema.get("validator")
        if validator and callable(validator):
            is_valid = validator(field_value)
            if not is_valid:
                result["valid"] = False
                error_msg = field_schema.get(
                    "error_message", f"Invalid value for '{field_name}'"
                )
                result["errors"][field_name] = error_msg

    return result