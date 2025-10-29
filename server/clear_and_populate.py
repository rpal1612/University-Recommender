"""
Clear existing test data and populate with 500 users
"""
from pymongo import MongoClient
import sys

# Connect to MongoDB
MONGODB_URI = 'mongodb+srv://admin:admin@cluster0.lgez1ci.mongodb.net/?appName=Cluster0'
MONGODB_DB_NAME = 'university_recommender'

print("Connecting to MongoDB...")
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]

print("\n" + "=" * 60)
print("CLEARING EXISTING TEST DATA")
print("=" * 60)

# Keep admin users, remove test users
admin_count = db.users.count_documents({'role': 'admin'})
test_user_count = db.users.count_documents({'role': 'user'})

print(f"\nFound {admin_count} admin users (will keep)")
print(f"Found {test_user_count} test users (will delete)")

# Delete test data
print("\nDeleting test users...")
result = db.users.delete_many({'role': 'user'})
print(f"  Deleted {result.deleted_count} users")

print("\nDeleting search history...")
result = db.search_history.delete_many({})
print(f"  Deleted {result.deleted_count} searches")

print("\nDeleting recommendations...")
result = db.recommendations.delete_many({})
print(f"  Deleted {result.deleted_count} recommendations")

print("\nDeleting wishlist items...")
result = db.wishlist.delete_many({})
print(f"  Deleted {result.deleted_count} wishlist items")

print("\n" + "=" * 60)
print("✅ CLEANUP COMPLETE")
print("=" * 60)

# Verify
print(f"\nRemaining users: {db.users.count_documents({})}")
print(f"Remaining searches: {db.search_history.count_documents({})}")
print(f"Remaining recommendations: {db.recommendations.count_documents({})}")

print("\nNow run: python populate_data_500.py")
