import bcrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from constants import FIXED_SALT
from Crypto.Cipher import AES


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed


def verify_password(password, hashed):
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.checkpw(password, hashed)


def derive_key_from_password(password, length=32):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=FIXED_SALT,
        iterations=1000,  # Use a high iteration count for security
        backend=default_backend()
    )
    key = kdf.derive(password.encode())  # Convert password to bytes and derive key
    return key


def encrypt_file(file_bytes, key):
    cipher = AES.new(key, AES.MODE_EAX, key)
    encrypted_data = cipher.encrypt(file_bytes)
    return encrypted_data


def decrypt_file(file_bytes, key):
    cipher = AES.new(key, AES.MODE_EAX, key)
    return cipher.decrypt(file_bytes)


def parse_request(text):
    details = {'valid': True,
               'request_type': '',
               'param': '',
               'admin-only': True}

    try:
        commands = list(text.split())
        major = commands[0]

        if major == 'list-groups':
            details['request_type'] = 'list-groups'
            details['admin-only'] = False
            return details

        if major == 'join-group':
            assert len(commands) == 2
            details['request_type'] = 'join-group'
            details['admin-only'] = False
            details['param'] = commands[1]
            return details

        if major == 'received-file':
            assert len(commands) == 2
            filename = commands[1]
            details['request_type'] = 'received-file'
            details['param'] = filename
            details['admin-only'] = False
            return details

        if major == 'my-groups':
            details['request_type'] = 'my-groups'
            details['admin-only'] = False
            return details



        details['admin-only'] = True

        if major == 'create-group':
            assert len(commands) == 2
            details['request_type'] = 'create-group'
            details['param'] = commands[1]
            return details
        if major == 'delete-group':
            assert len(commands) == 2
            details['request_type'] = 'delete-group'
            details['param'] = commands[1]
            return details

        if major == 'list-users':
            details['request_type'] = 'list-users'
            return details

        if major == 'view-requests':
            details['request_type'] = 'view-requests'
            return details

        if major == 'add':
            details['request_type'] = 'add'
            assert len(commands) == 3
            details['param'] = (commands[1], commands[2])
            return details

        if major == 'remove':
            details['request_type'] = 'remove'
            assert len(commands) == 3
            details['param'] = (commands[1], commands[2])
            return details

        if major == 'init':
            assert len(commands) >= 3
            details['request_type'] = 'init'
            groups = commands[2:]
            details['param'] = commands[1]
            details['groups'] = groups
            return details

        return {'valid': False}
    except:
        return {'valid': False}


def numerize_list(arr):
    if len(arr) == 0:
        return "List is empty!"
    result = "\n"
    idx = 1
    for i in arr:
        result += f"{idx}. {str(i)}\n"
        idx += 1
    return result
