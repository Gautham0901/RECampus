import sqlite3

def init_db():
    conn = sqlite3.connect('campus_connect.db')
    c = conn.cursor()
    
    # Create menu_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cafe_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image_url TEXT,
            available INTEGER DEFAULT 1,
            FOREIGN KEY (cafe_id) REFERENCES user (id)
        )
    ''')
    
    # Create orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            cafe_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (cafe_id) REFERENCES user (id)
        )
    ''')
    
    # Create order_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Insert default categories
    categories = ['Breakfast', 'Lunch', 'Snacks', 'Drinks', 'Hot Drinks']
    for category in categories:
        try:
            c.execute('INSERT INTO categories (name) VALUES (?)', (category,))
        except sqlite3.IntegrityError:
            pass
            
    # Add sample menu items for the food department
    try:
        c.execute('SELECT id FROM user WHERE role = "food" LIMIT 1')
        food_dept_id = c.fetchone()[0]
        
        sample_menu = [
            # Breakfast Items
            ('Masala Dosa', 'Crispy dosa with potato filling', 60.00, 'Breakfast'),
            ('Idli Sambar', 'Steamed rice cakes with sambar', 40.00, 'Breakfast'),
            ('Pongal', 'Traditional rice and lentil dish', 45.00, 'Breakfast'),
            ('Vada', 'Crispy lentil donuts with chutney', 30.00, 'Breakfast'),
            ('Poori Bhaji', 'Puffy bread with potato curry', 50.00, 'Breakfast'),
            
            # Lunch Items
            ('Veg Meals', 'Complete meal with rice, curry, and sides', 80.00, 'Lunch'),
            ('Veg Biryani', 'Fragrant rice with vegetables', 120.00, 'Lunch'),
            ('Chicken Biryani', 'Aromatic rice with chicken', 150.00, 'Lunch'),
            ('Curd Rice', 'Yogurt rice with tempering', 40.00, 'Lunch'),
            ('Chapati Curry', 'Wheat flatbread with vegetable curry', 70.00, 'Lunch'),
            
            # Snacks
            ('Samosa', 'Crispy pastry with spiced potato filling', 15.00, 'Snacks'),
            ('Vada Pav', 'Spicy potato patty in bun', 35.00, 'Snacks'),
            ('Pani Puri', 'Crispy shells with tangy water', 40.00, 'Snacks'),
            ('Bhel Puri', 'Puffed rice with chutneys', 35.00, 'Snacks'),
            ('French Fries', 'Crispy potato fries', 50.00, 'Snacks'),
            
            # Beverages
            ('Tea', 'Hot Indian tea', 15.00, 'Drinks'),
            ('Coffee', 'Fresh brewed coffee', 20.00, 'Drinks'),
            ('Lassi', 'Sweet yogurt drink', 30.00, 'Drinks'),
            ('Buttermilk', 'Spiced yogurt drink', 20.00, 'Drinks'),
            ('Fresh Lime Soda', 'Refreshing lime drink', 25.00, 'Drinks'),
            
            # Hot Drinks
            ('Hot Chocolate', 'Rich chocolate drink', 35.00, 'Hot Drinks'),
            ('Green Tea', 'Healthy green tea', 20.00, 'Hot Drinks'),
            ('Masala Tea', 'Spiced Indian tea', 20.00, 'Hot Drinks'),
            ('Filter Coffee', 'Traditional South Indian coffee', 25.00, 'Hot Drinks')
        ]
        
        for name, desc, price, category in sample_menu:
            c.execute('''
                INSERT OR IGNORE INTO menu_items 
                (cafe_id, name, description, price, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (food_dept_id, name, desc, price, category))
            
        print("Added sample menu items")
            
    except Exception as e:
        print(f"Error adding sample menu items: {e}")
            
    conn.commit()
    conn.close() 