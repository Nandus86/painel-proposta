from app.core.security import verify_password, get_password_hash

stored = '$2b$12$d3umsYkP5qzEiLS2WH3R.entM2VXAkiAkxCAF5U4Nrh3n93NOQna6'
print('Stored hash:', stored)

# Test 1: verify_password
print('verify_password("admin123"):', verify_password('admin123', stored))

# Test 2: new hash
new_hash = get_password_hash('test123')
print('New hash:', new_hash)
print('verify new:', verify_password('test123', new_hash))
