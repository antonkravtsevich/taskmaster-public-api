import hashlib

salt = 'f8382629e596cb23fc73970038f9e'


def get_hash(raw_pass):
    raw = raw_pass + salt
    raw_b = str.encode(raw)
    h = hashlib.sha512()
    h.update(raw_b)
    return h.hexdigest()