import string
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

# Define the set of characters to choose from when generating the key
characters = string.ascii_letters + string.digits + string.punctuation

# Generate a secret key with a specific length (e.g., 32 characters)
secret_key = ''.join(secrets.choice(characters) for _ in range(32))


def generate_pwd_hash(password):
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
    return hashed_password


def check_pwd_hash(hashed_password, my_password):
    return check_password_hash(hashed_password, my_password)
