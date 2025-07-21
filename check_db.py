import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('corps_attendance_dev.db')
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        if tables:
            # Check the users table specifically
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"\nNumber of users in database: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT email, full_name, is_admin FROM users LIMIT 5;")
                users = cursor.fetchall()
                print("\nFirst few users:")
                for user in users:
                    print(f"  - {user[1]} ({user[0]}) - Admin: {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
