"""
Clear all data from MongoDB and prepare for fresh population
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from config import Config

def main():
    print("Connecting to MongoDB...")
    db = Database(Config.MONGODB_URI, Config.MONGODB_DB_NAME)
    
    print("\n" + "="*60)
    print("CLEARING ALL DATA FROM DATABASE")
    print("="*60)
    
    # Count documents before deletion
    admin_count = db.users.count_documents({'role': 'admin'})
    user_count = db.users.count_documents({'role': 'user'})
    search_count = db.search_history.count_documents({})
    rec_count = db.recommendations.count_documents({})
    wishlist_count = db.wishlist.count_documents({})
    
    print(f"\nFound {admin_count} admin users (will keep)")
    print(f"Found {user_count} regular users (will delete)")
    print(f"Found {search_count} searches (will delete)")
    print(f"Found {rec_count} recommendations (will delete)")
    print(f"Found {wishlist_count} wishlist items (will delete)")
    
    # Delete test users (keep admin)
    print("\nDeleting all non-admin users...")
    result = db.users.delete_many({'role': 'user'})
    print(f"  Deleted {result.deleted_count} users")
    
    # Delete search history
    print("\nDeleting all search history...")
    result = db.search_history.delete_many({})
    print(f"  Deleted {result.deleted_count} searches")
    
    # Delete recommendations
    print("\nDeleting all recommendations...")
    result = db.recommendations.delete_many({})
    print(f"  Deleted {result.deleted_count} recommendations")
    
    # Delete wishlist items
    print("\nDeleting all wishlist items...")
    result = db.wishlist.delete_many({})
    print(f"  Deleted {result.deleted_count} wishlist items")
    
    print("\n" + "="*60)
    print("✅ DATABASE CLEARED SUCCESSFULLY")
    print("="*60)
    
    # Show remaining counts
    remaining_users = db.users.count_documents({})
    remaining_searches = db.search_history.count_documents({})
    remaining_recs = db.recommendations.count_documents({})
    
    print(f"\nRemaining users: {remaining_users} (admin only)")
    print(f"Remaining searches: {remaining_searches}")
    print(f"Remaining recommendations: {remaining_recs}")
    
    print("\n🚀 Now run: python server/populate_fresh_data.py")

if __name__ == "__main__":
    main()
