from database import Database
import config

db = Database(config.DATABASE_PATH)
profile = db.get_user_profile(123456)
print("Profile fetched:", profile)
