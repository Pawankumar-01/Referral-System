import random
import string


def generate_coupon_code(length: int = 9) -> str:
    """Generate a random 8-10 char uppercase alphanumeric coupon code."""
    chars = string.ascii_uppercase + string.digits
    # Avoid ambiguous characters
    chars = chars.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(random.choices(chars, k=length))
