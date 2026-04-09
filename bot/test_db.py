from database import Database

# Test mínimo: solo verifica que la instancia se crea y el método no revienta
db = Database()
profile = db.get_user_profile(123456)
print("Profile fetched:", profile)
