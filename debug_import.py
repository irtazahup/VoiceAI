try:
    import database
    print("Database module imported successfully")
    print("Available attributes:", dir(database))
    
    print("Testing get_db function...")
    db_generator = database.get_db()
    print("get_db function works!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
