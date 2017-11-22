"""Encrypt and decrypt datas"""

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import constants

def hash_str(obj):
    """Hashes a string"""
    if not obj:
        return None
    sha = SHA256.new()
    sha.update(str.encode(obj, 'utf-8'))
    return sha.digest()


def encrypt_str(obj):
    """Encrypts a string"""
    if not obj:
        return None
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(constants.ENCRYPTION_KEY, AES.MODE_CFB, iv)
    obj = iv + cipher.encrypt(str.encode(obj, 'utf-8'))
    return obj

def decrypt_str(obj):
    """Decrypts a string"""
    if not obj:
        return None
    iv = obj[0:AES.block_size]
    obj = obj[AES.block_size:]
    cipher = AES.new(constants.ENCRYPTION_KEY, AES.MODE_CFB, iv)
    obj = cipher.decrypt(obj).decode('utf-8')
    return obj

def encrypt_obj(obj):
    """Encrypts an object"""
    if not obj:
        return None
    fields = vars(obj)
    for key, value in fields.items():
        if not key.startswith("_") and key != "to_hash":
            if isinstance(value, str):
                if obj.to_hash and key in obj.to_hash:
                    value = hash_str(value)
                else:
                    value = encrypt_str(value)
                setattr(obj, key, value)
    return obj

def decrypt_obj(obj):
    """Decrypts an object"""
    if not obj:
        return None
    fields = vars(obj)
    for key, value in fields.items():
        if not key.startswith("_"):
            if isinstance(value, bytes):
                if not obj.to_hash or not key in obj.to_hash:
                    value = decrypt_str(value)
                    setattr(obj, key, value)
    return obj
