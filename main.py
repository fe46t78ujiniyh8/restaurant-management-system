import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
from PIL import Image, ImageTk
import os

class RestaurantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant Management System")
        self.root.geometry("1000x700")    

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Connect to SQLite database
        self.connect_to_database()

        # Current order status
        self.current_order_id = None
        self.current_order_items = {}
        self.is_transaction_active = False

        # Create tabs
        self.create_table_management_tab()
        self.create_order_tab()
        self.create_kitchen_tab()
        self.create_inventory_tab()
    
    # =========================================================================
    # Database Connection
    # =========================================================================

    def connect_to_database(self):
        try:
            self.connection = sqlite3.connect("restaurant_system.db")
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            print("Database connection successful")

            # -------------------------- Table Structure Creation --------------------------
            # 1. Tables Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_number TEXT UNIQUE NOT NULL,
                    capacity INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('Free', 'Occupied', 'Reserved', 'Under Maintenance')) DEFAULT 'Free'
                )
            ''')

            # 2. Dishes Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS dishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT,
                    description TEXT,
                    is_available INTEGER DEFAULT 1
                )
            ''')

            # 3. Ingredients Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    stock REAL NOT NULL,
                    low_stock_threshold REAL NOT NULL
                )
            ''')

            # 4. Dish-Ingredients Association Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS dish_ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dish_id INTEGER NOT NULL,
                    ingredient_id INTEGER NOT NULL,
                    quantity REAL NOT NULL,
                    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
                    UNIQUE (dish_id, ingredient_id)
                )
            ''')

            # 5. Orders Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER NOT NULL,
                    created_by TEXT NOT NULL,
                    order_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    total_amount REAL,
                    status TEXT DEFAULT 'Placed',
                    checkout_time TEXT,
                    payment_method TEXT,
                    received_amount REAL,
                    change_amount REAL,
                    FOREIGN KEY (table_id) REFERENCES tables(id) ON UPDATE CASCADE ON DELETE CASCADE
                )
            ''')

            # 6. Order Items Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    dish_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    subtotal REAL NOT NULL,
                    status TEXT DEFAULT 'Pending',
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON UPDATE CASCADE
                )
            ''')

            # 7. Inventory Logs Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ingredient_id INTEGER NOT NULL,
                    change_type TEXT NOT NULL CHECK(change_type IN ('Inbound','Outbound','Adjustment')),
                    quantity REAL NOT NULL,
                    old_stock REAL NOT NULL,
                    new_stock REAL NOT NULL,
                    reason TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON UPDATE CASCADE
                )
            ''')
            
            self.cursor.execute("PRAGMA table_info(orders)")
            order_columns = [row[1] for row in self.cursor.fetchall()]
            if "received_amount" not in order_columns:
                self.cursor.execute("ALTER TABLE orders ADD COLUMN received_amount REAL")
            if "change_amount" not in order_columns:
                self.cursor.execute("ALTER TABLE orders ADD COLUMN change_amount REAL")

            # -------------------------- Data Initialization --------------------------
            # Insert regular sample dishes
            self.cursor.execute("SELECT COUNT(*) FROM dishes")
            if self.cursor.fetchone()[0] == 0:
                sample_dishes = [
                    ("Kung Pao Chicken", 38.0, "Sichuan Cuisine", "Classic Sichuan dish, spicy and fragrant"),
                    ("Yu-Shiang Shredded Pork", 32.0, "Sichuan Cuisine", "Yu-Shiang flavor, perfect with rice"),
                    ("Mapo Tofu", 28.0, "Sichuan Cuisine", "Spicy and fragrant, tender tofu"),
                    ("Twice-Cooked Pork", 36.0, "Sichuan Cuisine", "Fat but not greasy, spicy and delicious"),
                    ("Boiled Fish with Spicy Sauce", 48.0, "Sichuan Cuisine", "Tender fish, spicy and fragrant")
                ]
                self.cursor.executemany("INSERT INTO dishes (name, price, category, description) VALUES (?, ?, ?, ?)", sample_dishes)

            # Insert regular ingredients
            self.cursor.execute("SELECT COUNT(*) FROM ingredients")
            if self.cursor.fetchone()[0] == 0:
                sample_ingredients = [
                    ("Chicken", "kg", 50, 10), ("Pork", "kg", 40, 5), ("Tofu", "kg", 30, 5),
                    ("Green Pepper", "kg", 20, 5), ("Onion", "kg", 15, 3), ("Chili Pepper", "kg", 10, 2),
                    ("Peanuts", "kg", 10, 2), ("Fish Fillet", "kg", 20, 5), ("Garlic", "kg", 5, 1), ("Ginger", "kg", 5, 1)
                ]
                self.cursor.executemany("INSERT INTO ingredients (name, unit, stock, low_stock_threshold) VALUES (?, ?, ?, ?)", sample_ingredients)

            # Insert regular recipes
            self.cursor.execute("SELECT COUNT(*) FROM dish_ingredients")
            if self.cursor.fetchone()[0] == 0:
                sample_dish_ingredients = [
                    (1, 1, 0.3), (1, 4, 0.1), (1, 5, 0.05), (1, 7, 0.05), # Kung Pao Chicken
                    (2, 2, 0.3), (2, 4, 0.1), (2, 5, 0.05), (2, 9, 0.02), (2, 10, 0.01), # Yu-Shiang Shredded Pork
                    (3, 3, 0.25), (3, 2, 0.05), (3, 6, 0.02), # Mapo Tofu
                    (4, 2, 0.3), (4, 4, 0.1), (4, 9, 0.02), (4, 10, 0.01), # Twice-Cooked Pork
                    (5, 8, 0.3), (5, 4, 0.1), (5, 9, 0.02), (5, 10, 0.01), (5, 6, 0.02) # Boiled Fish with Spicy Sauce
                ]
                self.cursor.executemany("INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity) VALUES (?, ?, ?)", sample_dish_ingredients)

            # Insert tables
            self.cursor.execute("SELECT COUNT(*) FROM tables")
            if self.cursor.fetchone()[0] == 0:
                sample_tables = [("Table 1", 4), ("Table 2", 6), ("Table 3", 2), ("Table 4", 8), ("Table 5", 4)]
                self.cursor.executemany("INSERT INTO tables (table_number, capacity) VALUES (?, ?)", sample_tables)

            # -------------------------- Core Modification: Initialize Premade Dish Data --------------------------
            self.initialize_premade_data()

            self.connection.commit()
            print("Database initialization completed (including premade dishes)")
            self.load_table_map()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Initialization failed: {str(e)}")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Unknown error: {str(e)}")
            self.root.destroy()

    def initialize_premade_data(self):
        """
        Initialize premade dish data.
        Logic:
        1. Add 'xxx Meal Kit' to the ingredients table.
        2. Add 'xxx (Premade)' to the dishes table.
        3. Establish the relationship of 1 dish serving = 1 meal kit in the association table.
        """
        print("Checking premade dish data...")
        
        # Define premade dish data structure: (dish name, price, ingredient name, stock quantity, threshold)
        premade_items = [
            ("Taiwanese Braised Pork Rice (Premade)", 25.0, "Braised Pork Meal Kit", 50, 5),
            ("Braised Beef Rice (Premade)", 28.0, "Braised Beef Meal Kit", 40, 5),
            ("Italian Meat Sauce Pasta (Premade)", 26.0, "Meat Sauce Pasta Combo Kit", 30, 5),
            ("Cantonese Sausage Fried Rice (Premade)", 22.0, "Sausage Fried Rice Meal Kit", 50, 10)
        ]

        for dish_name, price, ing_name, stock, threshold in premade_items:
            # 1. Ensure the ingredient exists
            self.cursor.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,))
            res_ing = self.cursor.fetchone()
            if not res_ing:
                self.cursor.execute(
                    "INSERT INTO ingredients (name, unit, stock, low_stock_threshold) VALUES (?, 'Bag', ?, ?)",
                    (ing_name, stock, threshold)
                )
                ingredient_id = self.cursor.lastrowid
                print(f"  + Added premade ingredient: {ing_name}")
            else:
                ingredient_id = res_ing['id']

            # 2. Ensure the dish exists
            self.cursor.execute("SELECT id FROM dishes WHERE name = ?", (dish_name,))
            res_dish = self.cursor.fetchone()
            if not res_dish:
                self.cursor.execute(
                    "INSERT INTO dishes (name, price, category, description) VALUES (?, ?, 'Premade Dishes', 'Quick and delicious, ready to eat after heating')",
                    (dish_name, price)
                )
                dish_id = self.cursor.lastrowid
                print(f"  + Added premade dish: {dish_name}")
            else:
                dish_id = res_dish['id']

            # 3. Ensure the association exists (1 dish serving consumes 1 bag of ingredient)
            self.cursor.execute(
                "SELECT id FROM dish_ingredients WHERE dish_id = ? AND ingredient_id = ?", 
                (dish_id, ingredient_id)
            )
            if not self.cursor.fetchone():
                self.cursor.execute(
                    "INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity) VALUES (?, ?, 1.0)",
                    (dish_id, ingredient_id)
                )
                print(f"  + Established association: {dish_name} -> {ing_name} (1:1)")
    
    def load_table_map(self):
        """Load the mapping of table numbers to IDs (required for order management, avoiding hard-coded IDs)"""
        try:
            self.cursor.execute("SELECT id, table_number FROM tables")
            tables = self.cursor.fetchall()
            self.table_map = {table['table_number']: table['id'] for table in tables}
            print(f"🪑 Loaded {len(self.table_map)} table mappings")
        except Exception as e:
            print(f"Failed to load table mappings: {e}")
            self.table_map = {}

    # =========================================================================
    # Table Management Tab 
    # =========================================================================
    def create_table_management_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Table Management")

        # Buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Add Table", command=self.add_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Table", command=self.delete_table).pack(side=tk.LEFT, padx=5)

        # Search/Filter
        search_frame = ttk.Frame(button_frame)
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="Search Table No.:").pack(side=tk.LEFT)
        self.table_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.table_search_var, width=15).pack(side=tk.LEFT)
        ttk.Button(search_frame, text="Search", command=self.refresh_tables).pack(side=tk.LEFT)

        filter_frame = ttk.Frame(button_frame)
        filter_frame.pack(side=tk.RIGHT)
        ttk.Label(filter_frame, text="Status:").pack(side=tk.LEFT)
        self.table_status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.table_status_var,
                                    values=["All", "Free", "Occupied"], width=10)
        status_combo.pack(side=tk.LEFT)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_tables())

        # Table List (with scrollbar)
        table_container = ttk.Frame(tab)
        table_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create vertical scrollbar
        v_scrollbar_table = ttk.Scrollbar(table_container, orient=tk.VERTICAL)
        v_scrollbar_table.pack(side=tk.RIGHT, fill=tk.Y)

        # Create horizontal scrollbar
        h_scrollbar_table = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        h_scrollbar_table.pack(side=tk.BOTTOM, fill=tk.X)

        self.table_tree = ttk.Treeview(table_container, 
                                    columns=("id", "table_number", "capacity", "status"), 
                                    show="headings",
                                    yscrollcommand=v_scrollbar_table.set,
                                    xscrollcommand=h_scrollbar_table.set)
        
        # Configure scrollbars
        v_scrollbar_table.config(command=self.table_tree.yview)
        h_scrollbar_table.config(command=self.table_tree.xview)

        self.table_tree.heading("id", text="ID")
        self.table_tree.heading("table_number", text="Table Number")
        self.table_tree.heading("capacity", text="Capacity")
        self.table_tree.heading("status", text="Status")
        
        self.table_tree.pack(fill=tk.BOTH, expand=True)
        self.table_tree.bind("<Double-1>", self.edit_table_status)

        self.refresh_tables()
    
    def add_table(self):
        # Table number validation: must be an integer greater than 0
        num = simpledialog.askinteger("Add Table", "Table Number (must be an integer greater than 0):")
        if num is None:  # User canceled input
            return
        if num <= 0:
            messagebox.showerror("Error", "Table number must be an integer greater than 0")
            return

        # Capacity validation: must be an integer greater than 0
        cap = simpledialog.askinteger("Add Table", "Capacity (must be an integer greater than 0):")
        if cap is None:  # User canceled input
            return
        if cap <= 0:
            messagebox.showerror("Error", "Capacity must be an integer greater than 0")
            return

        try:
            table_number = f"Table {num}"
            self.cursor.execute("INSERT INTO tables (table_number, capacity, status) VALUES (?, ?, 'Free')", (table_number, cap))
            self.connection.commit()
            self.refresh_tables()
            # Refresh table selection on order page
            self.refresh_table_combo()
            messagebox.showinfo("Success", f"Added successfully: {table_number}")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", f"Table {table_number} already exists")

    def delete_table(self):
        sel = self.table_tree.selection()
        if not sel: return
        table_data = self.table_tree.item(sel[0])["values"]
        if not table_data: return
        
        table_id = table_data[0]
        table_number = table_data[1]

        # Check if there are unfinished orders
        self.cursor.execute("""
            SELECT COUNT(*) FROM orders 
            WHERE table_id = ? AND status IN ('Placed', 'In Progress', 'Served')
        """, (table_id,))
        if self.cursor.fetchone()[0] > 0:
            messagebox.showerror("Error", "This table has unfinished orders and cannot be deleted!")
            return

        if messagebox.askyesno("Confirmation", f"Are you sure to delete table {table_number}? It cannot be recovered after deletion!"):
            self.cursor.execute("DELETE FROM tables WHERE id=?", (table_id,))
            self.connection.commit()
            self.refresh_tables()
            # Refresh table list in order management
            self.refresh_table_combo()
            messagebox.showinfo("Success", "Table deleted successfully")
    
    def refresh_tables(self):
        for item in self.table_tree.get_children():
            self.table_tree.delete(item)
        sql = "SELECT * FROM tables WHERE 1=1"
        params = []
        search = self.table_search_var.get()
        if search:
            sql += " AND table_number LIKE ?"
            params.append(f"%{search}%")
        status = self.table_status_var.get()
        if status != "All":
            sql += " AND status=?"
            params.append(status)
        self.cursor.execute(sql, params)
        for row in self.cursor.fetchall():
            self.table_tree.insert("", "end", values=tuple(row))

    def edit_table_status(self, event):
        sel = self.table_tree.selection()
        if not sel:
            return
        row = self.table_tree.item(sel[0])["values"]
        table_id, table_number, capacity, status = row

        # Pop up number input dialog
        choice = simpledialog.askinteger(
            "Edit Status",
            "Table {} Current Status: {}\n\nPlease enter a number to select new status:\n1 = Free\n2 = Occupied".format(table_number, status)
        )

        status_map = {
            1: "Free",
            2: "Occupied",
        }

        if choice not in status_map:
            messagebox.showerror("Error", "Invalid input, please enter 1 or 2")
            return

        new_status = status_map[choice]

        self.cursor.execute("UPDATE tables SET status=? WHERE id=?", (new_status, table_id))
        self.connection.commit()
        self.refresh_tables()

    # =========================================================================
    # Order Management Tab 
    # =========================================================================
    def create_order_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Order Management")

        # total_var to display total price
        self.total_var = tk.StringVar(value="Total: 0 CNY")
        ttk.Label(tab, textvariable=self.total_var, font=("", 12, "bold")).pack(pady=5)

        # Table selection
        table_frame = ttk.Frame(tab)
        table_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(table_frame, text="Select Table:").pack(side=tk.LEFT)
        self.selected_table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(table_frame, textvariable=self.selected_table_var, width=15)
        self.table_combo.pack(side=tk.LEFT, padx=5)
        self.table_combo.bind("<<ComboboxSelected>>", self.on_table_selected)
        
        # Table order info display
        self.table_order_info_var = tk.StringVar(value="")
        ttk.Label(table_frame, textvariable=self.table_order_info_var, foreground="blue").pack(side=tk.LEFT, padx=20)

        # Create left-right split frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Dish list
        left_frame = ttk.LabelFrame(main_frame, text="Dish List")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Dish list scrollbars
        dish_v_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        dish_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        dish_h_scrollbar = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL)
        dish_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.dish_tree = ttk.Treeview(left_frame, 
                                    columns=("id", "name", "price"), 
                                    show="headings",
                                    yscrollcommand=dish_v_scrollbar.set,
                                    xscrollcommand=dish_h_scrollbar.set)
        dish_v_scrollbar.config(command=self.dish_tree.yview)
        dish_h_scrollbar.config(command=self.dish_tree.xview)

        self.dish_tree.heading("id", text="ID")
        self.dish_tree.heading("name", text="Name")
        self.dish_tree.heading("price", text="Price")
        
        self.dish_tree.pack(fill=tk.BOTH, expand=True)
        self.dish_tree.bind("<Double-1>", self.add_dish_to_order)

        # Right: Order view
        right_frame = ttk.LabelFrame(main_frame, text="Current Order")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Order view scrollbars
        order_v_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        order_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        order_h_scrollbar = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL)
        order_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.order_tree = ttk.Treeview(right_frame, 
                                    columns=("name", "price", "quantity", "subtotal", "status"), 
                                    show="headings",
                                    yscrollcommand=order_v_scrollbar.set,
                                    xscrollcommand=order_h_scrollbar.set)
        order_v_scrollbar.config(command=self.order_tree.yview)
        order_h_scrollbar.config(command=self.order_tree.xview)

        self.order_tree.heading("name", text="Name")
        self.order_tree.heading("price", text="Price")
        self.order_tree.heading("quantity", text="Quantity")
        self.order_tree.heading("subtotal", text="Subtotal")
        self.order_tree.heading("status", text="Status")
        
        self.order_tree.pack(fill=tk.BOTH, expand=True)

        # Order buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Create Order", command=self.create_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Submit Order", command=self.submit_order).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Dish", command=self.remove_one_dish).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Checkout & Print", command=self.checkout_order).pack(side=tk.LEFT, padx=5)

        self.refresh_dishes()
        self.refresh_table_combo()

    # Modify the on_table_selected method to ensure storing the item_id of order items
    def on_table_selected(self, event=None):
        """When a table is selected, display the order dishes for that table"""
        table_number = self.selected_table_var.get()
        if not table_number:
            self.table_order_info_var.set("Please select a table")
            self.clear_order_display()
            return

        if table_number not in self.table_map:
            self.table_order_info_var.set("Table does not exist")
            self.clear_order_display()
            return

        table_id = self.table_map[table_number]

        try:
            # Query all unpaid orders for this table
            self.cursor.execute("""
                SELECT o.id, o.status, o.total_amount
                FROM orders o
                WHERE o.table_id = ? AND o.status IN ('Placed', 'In Progress', 'Served')
                ORDER BY o.id DESC
            """, (table_id,))
            
            orders = self.cursor.fetchall()
            
            # Clear currently displayed order
            self.clear_order_display()
            self.current_order_items = {}
            
            if orders:
                order_info = []
                total_amount = 0
                
                # Iterate through all orders to get dish information
                for order in orders:
                    order_id = order['id']
                    status = order['status']
                    total_amount += order['total_amount'] if order['total_amount'] else 0
                    
                    # Query all dishes for this order (including order item ID)
                    self.cursor.execute("""
                        SELECT oi.id, oi.dish_id, d.name, d.price, oi.quantity, oi.subtotal, oi.status
                        FROM order_items oi
                        JOIN dishes d ON oi.dish_id = d.id
                        WHERE oi.order_id = ?
                    """, (order_id,))
                    
                    items = self.cursor.fetchall()
                    
                    for item in items:
                        item_id = item['id']  # Get order item ID
                        dish_id = item['dish_id']
                        name = item['name']
                        price = float(item['price'])
                        quantity = item['quantity']
                        subtotal = float(item['subtotal'])
                        item_status = item['status']
                        
                        # Use composite key containing item_id to ensure uniqueness (key modification)
                        key = f"{dish_id}_{order_id}_{item_id}"
                        self.current_order_items[key] = {
                            "item_id": item_id,  # Store order item ID
                            "name": name, 
                            "price": price, 
                            "quantity": quantity, 
                            "subtotal": subtotal,
                            "status": item_status,
                            "order_id": order_id,
                            "dish_id": dish_id
                        }
                        
                        # Add to order view display
                        self.order_tree.insert(
                            "",
                            "end",
                            values=(
                                name,
                                price,
                                quantity,
                                subtotal,
                                item_status
                            )
                        )
                    
                    status_map = {
                        'Placed': 'Pending',
                        'In Progress': 'In Progress', 
                        'Served': 'Completed'
                    }
                    status_display = status_map.get(status, status)
                    order_info.append(f"Order {order_id} ({status_display})")
                
                display_text = f"Current Orders: {', '.join(order_info)}"
                self.table_order_info_var.set(display_text)
                self.total_var.set(f"Total: {total_amount:.2f} CNY")
                
            else:
                self.table_order_info_var.set("No current orders")
                self.total_var.set("Total: 0.00 CNY")
                
        except Exception as e:
            print(f"Error in on_table_selected: {e}")
            self.table_order_info_var.set("Query error")
            self.clear_order_display()

    def clear_order_display(self):
        """Clear order display"""
        for i in self.order_tree.get_children():
            self.order_tree.delete(i)
        self.current_order_items = {}
        self.total_var.set("Total: 0.00 CNY")
        self.current_order_id = None

    def refresh_table_combo(self):
        self.cursor.execute("SELECT id, table_number FROM tables WHERE status IN ('Free', 'Occupied')")
        tables = self.cursor.fetchall()
        self.table_map = {t["table_number"]: t["id"] for t in tables}
        self.table_combo['values'] = list(self.table_map.keys())
        if tables:
            self.table_combo.current(0)
            # Display table order information during initialization
            self.root.after(100, self.on_table_selected)
    
    def refresh_dishes(self):
        for i in self.dish_tree.get_children():
            self.dish_tree.delete(i)
        self.cursor.execute("SELECT id, name, price FROM dishes WHERE is_available=1")
        for row in self.cursor.fetchall():
            self.dish_tree.insert("", "end", values=tuple(row))
    
    def create_order(self):
        table_number = self.selected_table_var.get()
        if not table_number:
            messagebox.showwarning("Prompt", "Please select a table")
            return

        table_id = self.table_map[table_number]

        # Insert order with explicit current time
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert order
        self.cursor.execute(
            "INSERT INTO orders (table_id, created_by, order_date) VALUES (?, ?, ?)",
            (table_id, "System Operator", current_time)
        )
        self.connection.commit()

        self.current_order_id = self.cursor.lastrowid
        messagebox.showinfo("Order", f"Order created, ID: {self.current_order_id}")

        # Set table status to Occupied
        self.cursor.execute("UPDATE tables SET status='Occupied' WHERE id=?", (table_id,))
        self.connection.commit()
        self.refresh_tables()
        
        # Reload order display
        self.on_table_selected()

    # =========================================================================
    # Inventory Check and Deduction Logic Modification
    # =========================================================================
    def check_and_deduct_ingredients(self, dish_id, quantity=1, deduct=False):
        """
        Check and optionally deduct ingredient inventory, return the check result
        Only when deduct=True will the inventory be actually deducted
        """
        try:
            # Get all the ingredients needed for the dish
            self.cursor.execute("""
                SELECT di.ingredient_id, di.quantity, i.name, i.stock, i.unit 
                FROM dish_ingredients di
                JOIN ingredients i ON di.ingredient_id = i.id
                WHERE di.dish_id = ?
            """, (dish_id,))
            
            ingredients = self.cursor.fetchall()
            if not ingredients:
                messagebox.showwarning("Warning", "This dish has no ingredients configured and cannot be processed.")
                return False
            
            # Check if the inventory is sufficient
            insufficient = []
            for ing in ingredients:
                required = ing['quantity'] * quantity
                if ing['stock'] < required:
                    insufficient.append(
                        f"{ing['name']}Not Enough (Demand: {required}{ing['unit']}, Current: {ing['stock']}{ing['unit']})"
                    )
            
            if insufficient:
                if not deduct:  # Return specific deficiency information in check-only mode
                    return {"success": False, "message": "\n".join(insufficient)}
                return False
            
            # If stock deduction is required and there is sufficient stock
            if deduct:
                for ing in ingredients:
                    ingredient_id = ing['ingredient_id']
                    required = ing['quantity'] * quantity
                    old_stock = ing['stock']
                    new_stock = old_stock - required
                    
                    # Update inventory
                    self.cursor.execute(
                        "UPDATE ingredients SET stock = ? WHERE id = ?",
                        (new_stock, ingredient_id)
                    )
                    
                    # Record inventory movement log
                    self.cursor.execute("""
                        INSERT INTO inventory_logs 
                        (ingredient_id, change_type, quantity, old_stock, new_stock, reason, created_by)
                        VALUES (?, 'Stock Out', ?, ?, ?, '订单消耗', '系统操作员')
                    """, (ingredient_id, required, old_stock, new_stock))
                
                self.connection.commit()
            
            return {"success": True} if not deduct else True
            
        except Exception as e:
            messagebox.showerror("Error", f"Inventory processing failed: {str(e)}")
            return {"success": False, "message": str(e)} if not deduct else False

    # =========================================================================
    # Order management related modifications
    # =========================================================================
    def add_dish_to_order(self, event=None):
        """Add dishes to order (add only, no inventory check)"""
        table_number = self.selected_table_var.get()
        if not table_number:
            messagebox.showwarning("Warning", "Please select a table first")
            return
            
        # Get the latest unfinished order for this table
        table_id = self.table_map[table_number]
        self.cursor.execute("""
            SELECT id FROM orders 
            WHERE table_id = ? AND status IN ('Placed', 'In Progress', 'Served')
            ORDER BY id DESC LIMIT 1
        """, (table_id,))
        
        order_result = self.cursor.fetchone()
        if not order_result:
            messagebox.showwarning("Warning", "Please create an order for this table first.")
            return
            
        order_id = order_result['id']
        
        sel = self.dish_tree.selection()
        if not sel: return
            
        dish_id, name, price = self.dish_tree.item(sel[0], "values")
        dish_id = int(dish_id)
        price = float(price)

        try:
            # Only add dishes to the order without checking inventory
            self.cursor.execute(
                "INSERT INTO order_items (order_id, dish_id, quantity, subtotal, status) VALUES (?, ?, ?, ?, 'Pending')",
                (order_id, dish_id, 1, price)
            )
            
            # Update the total order amount
            self.cursor.execute("""
                UPDATE orders 
                SET total_amount = COALESCE(total_amount, 0) + ? 
                WHERE id = ?
            """, (price, order_id))
            
            self.connection.commit()
            # Refresh order display
            self.on_table_selected()
            
        except Exception as e:
            self.connection.rollback()
            messagebox.showerror("Error", f"Failed to add dish: {str(e)}")
    
    def remove_one_dish(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Prompt", "Please select the dish to delete")
            return

        item_values = self.order_tree.item(sel[0])["values"]
        if not item_values:
            return
            
        name, price, quantity, subtotal, status = item_values

        # Check dish status, only dishes with status 'Pending' can be deleted
        if status != "Pending":
            messagebox.showwarning("Prompt", f"Dish '{name}' status is '{status}', cannot be deleted")
            return

        # Match corresponding item_id from current_order_items (ensure on_table_selected has loaded item_id)
        item_id = None
        target_price = float(price)
        target_quantity = int(quantity)
        target_subtotal = float(subtotal)
        
        for item in self.current_order_items.values():
            if (item["name"] == name 
                and abs(item["price"] - target_price) < 0.01 
                and item["quantity"] == target_quantity 
                and abs(item["subtotal"] - target_subtotal) < 0.01 
                and item["status"] == status):
                item_id = item.get("item_id")
                break

        if not item_id:
            messagebox.showwarning("Prompt", "Corresponding dish information not found")
            return

        try:
            # 1. Get order ID associated with the order item
            self.cursor.execute("SELECT order_id FROM order_items WHERE id = ?", (item_id,))
            result = self.cursor.fetchone()
            if not result:
                messagebox.showerror("Error", "Dish record not found")
                return
            order_id = result['order_id']

            # 2. Delete the order item
            self.cursor.execute("DELETE FROM order_items WHERE id = ?", (item_id,))

            # 3. Recalculate total order amount
            self.cursor.execute("SELECT SUM(subtotal) as new_total FROM order_items WHERE order_id = ?", (order_id,))
            total_result = self.cursor.fetchone()
            new_total = total_result['new_total'] or 0

            # 4. Check order status and update total amount
            self.cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
            order_status = self.cursor.fetchone()['status']
            is_submitted = order_status in ('Placed', 'In Progress', 'Served')

            if is_submitted:
                self.cursor.execute("UPDATE orders SET total_amount = ? WHERE id = ?", (new_total, order_id))

                # 5. If total amount is 0, delete order and associated items
                if new_total <= 0:
                    self.cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
                    self.cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                    self.connection.commit()
                    messagebox.showinfo("Prompt", "Order total amount is now 0, order has been automatically deleted")
                    self.refresh_order_display()
                    return

            # Commit transaction
            self.connection.commit()
            messagebox.showinfo("Success", "Dish deleted successfully, order total has been updated")
            
            # 6. Refresh display
            self.refresh_order_display()

        except Exception as e:
            self.connection.rollback()
            messagebox.showerror("Error", f"Deletion failed: {str(e)}")

    def refresh_order_display(self):
        """Refresh order display: update order item list, total price and status information"""
        # Clear existing order display
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # Clear total price display
        self.total_var.set("Total: 0.00 CNY")
        
        # Get currently selected table
        current_table = self.selected_table_var.get()
        if not current_table:
            self.table_order_info_var.set("Please select a table to view orders")
            return
        
        table_id = self.table_map.get(current_table)
        if not table_id:
            self.table_order_info_var.set("Table information not found")
            return
        
        try:
            # Query active orders for current table
            self.cursor.execute("""
                SELECT id, status, total_amount FROM orders 
                WHERE table_id = ? AND status != 'Paid'
            """, (table_id,))
            active_orders = self.cursor.fetchall()
            
            if not active_orders:
                self.table_order_info_var.set("No active orders for current table")
                return
            
            # Handle multiple orders
            order_info = []
            total_amount = 0
            self.current_order_items = {}  # Reset current order items
            
            for order in active_orders:
                order_id = order['id']
                order_status = order['status']
                total_amount += order['total_amount'] or 0
                
                # Update order status display
                status_map = {'Placed': 'Pending', 'In Progress': 'In Progress', 'Served': 'Completed'}
                order_info.append(f"Order {order_id} ({status_map.get(order_status, order_status)})")
                
                # Load order items
                self.cursor.execute("""
                    SELECT oi.id, oi.dish_id, d.name, d.price, oi.quantity, oi.subtotal, oi.status
                    FROM order_items oi
                    JOIN dishes d ON oi.dish_id = d.id
                    WHERE oi.order_id = ?
                """, (order_id,))
                
                for item in self.cursor.fetchall():
                    item_id = item['id']
                    dish_id = item['dish_id']
                    name = item['name']
                    price = float(item['price'])
                    quantity = item['quantity']
                    subtotal = float(item['subtotal'])
                    item_status = item['status']
                    
                    # Update current_order_items
                    key = f"{dish_id}_{order_id}_{item_id}"
                    self.current_order_items[key] = {
                        "item_id": item_id,
                        "name": name,
                        "price": price,
                        "quantity": quantity,
                        "subtotal": subtotal,
                        "status": item_status,
                        "order_id": order_id,
                        "dish_id": dish_id
                    }
                    
                    # Add to order tree display
                    self.order_tree.insert("", "end", values=(
                        name, price, quantity, subtotal, item_status
                    ))
            
            # Update total price and status display
            self.table_order_info_var.set(f"Current Orders: {', '.join(order_info)}")
            self.total_var.set(f"Total: {total_amount:.2f} CNY")
            
            # Refresh kitchen orders
            self.refresh_kitchen_orders()

        except Exception as e:
            messagebox.showerror("Refresh Failed", f"Error updating order display: {str(e)}")

    def submit_order(self):
        """Submit order - Check if all dishes have sufficient stock at this time (using allowed status values)"""
        table_number = self.selected_table_var.get()
        if not table_number:
            messagebox.showwarning("Warning", "Please select a table")
            return

        table_id = self.table_map[table_number]
        
        # Retrieve the current table's unsubmitted orders (orders with the status 'Placed')
        self.cursor.execute("""
            SELECT id FROM orders 
            WHERE table_id = ? AND status = 'Placed'
            ORDER BY id DESC LIMIT 1
        """, (table_id,))
        
        order_result = self.cursor.fetchone()
        if not order_result:
            messagebox.showwarning("Warning", "No orders available for submission")
            return
            
        order_id = order_result['id']
        
        # Retrieve all pending dishes in the order
        self.cursor.execute("""
            SELECT oi.dish_id, oi.quantity, d.name 
            FROM order_items oi
            JOIN dishes d ON oi.dish_id = d.id
            WHERE oi.order_id = ? AND oi.status = 'Pending'
        """, (order_id,))
        
        order_items = self.cursor.fetchall()
        if not order_items:
            messagebox.showwarning("Warning", "There are no dishes to be submitted in the order.")
            return
        
        # Check the inventory of all dishes to ensure sufficient stock
        insufficient_items = []
        for item in order_items:
            dish_id = item['dish_id']
            quantity = item['quantity']
            dish_name = item['name']
            
            check_result = self.check_and_deduct_ingredients(dish_id, quantity)
            if not check_result["success"]:
                insufficient_items.append(f"Dish《{dish_name}》: {check_result['message']}")
        
        if insufficient_items:
            messagebox.showerror("Insufficient stock", 
                            "The following dishes are out of stock and cannot be ordered:\n" + "\n".join(insufficient_items))
            return
        
        # Inventory check passed, updating order status to 'In Progress' (using database-allowed statuses)
        try:
            self.cursor.execute(
                "UPDATE orders SET status = 'In Progress' WHERE id = ?", 
                (order_id,)
            )
            self.connection.commit()
            messagebox.showinfo("Success", f"Order {order_id} Submission successful！")
            self.on_table_selected()  # Refresh order display
        except Exception as e:
            self.connection.rollback()
            messagebox.showerror("Error", f"Failed to submit order: {str(e)}")

    def checkout_order(self):
        """Handle order checkout process"""
        table_number = self.selected_table_var.get()
        if not table_number:
            messagebox.showwarning("Prompt", "Please select a table")
            return

        table_id = self.table_map.get(table_number)
        if not table_id:
            messagebox.showerror("Error", "Table information does not exist")
            return

        # Get unpaid orders for current table
        self.cursor.execute("""
            SELECT id, total_amount FROM orders 
            WHERE table_id = ? AND status IN ('Placed', 'In Progress', 'Served')
        """, (table_id,))
        
        orders = self.cursor.fetchall()
        if not orders:
            messagebox.showinfo("Prompt", "No orders available for checkout at this table")
            return

        # Calculate total amount
        total_amount = sum(order['total_amount'] or 0 for order in orders)
        if total_amount <= 0:
            messagebox.showinfo("Prompt", "Order total amount is 0, no need to checkout")
            return

        # Create payment method selection dialog
        self.show_payment_method_dialog(orders, total_amount, table_id)
    
    def show_payment_method_dialog(self, orders, total_amount, table_id):
            """Display payment method selection dialog"""
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Payment Method")
            dialog.geometry("300x200")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()  # Modal window

            # Center display
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
            y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
            dialog.geometry(f"+{x}+{y}")

            ttk.Label(dialog, text=f"Total Order Amount: ¥{total_amount:.2f}", font=("Arial", 12, "bold")).pack(pady=20)

            # Payment method button frame
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(expand=True)

            # WeChat Pay button
            ttk.Button(
                btn_frame, 
                text="WeChat Pay", 
                width=15,
                command=lambda: self.process_wechat_alipay_payment(dialog, orders, total_amount, table_id, "WeChat Pay")
            ).pack(pady=5)

            # Alipay button
            ttk.Button(
                btn_frame, 
                text="Alipay", 
                width=15,
                command=lambda: self.process_wechat_alipay_payment(dialog, orders, total_amount, table_id, "Alipay")
            ).pack(pady=5)

            # Cash Payment button
            ttk.Button(
                btn_frame, 
                text="Cash Payment", 
                width=15,
                command=lambda: self.process_cash_payment(dialog, orders, total_amount, table_id)
            ).pack(pady=5)
    
    def process_wechat_alipay_payment(self, dialog, orders, total_amount, table_id, payment_method):
        """Process WeChat or Alipay payment, display amount and QR code"""
        dialog.destroy()  # Close previous window
        
        # Create payment window (display amount and QR code)
        pay_window = tk.Toplevel(self.root)
        pay_window.title(f"{payment_method} Payment")
        pay_window.geometry("400x500")
        pay_window.transient(self.root)
        pay_window.grab_set()

        # 1. Display payment amount
        ttk.Label(
            pay_window, 
            text=f"Please Pay: {total_amount:.2f} CNY", 
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        # 2. Display payment QR code
        qrcode_frame = ttk.Frame(pay_window)
        qrcode_frame.pack(pady=10)

        # Select corresponding QR code image based on payment method (WeChat: wechat_qrcode.jpg, Alipay: alipay_qrcode.jpg)
        image_path = f"{payment_method.lower().replace(' ', '_')}_qrcode.jpg"

        try:
            # Open and resize image
            img = Image.open(image_path)
            img = img.resize((250, 250), Image.LANCZOS)  # High-quality resizing
            photo = ImageTk.PhotoImage(img)
            
            # Display image
            qrcode_label = ttk.Label(qrcode_frame, image=photo)
            qrcode_label.image = photo  # Keep reference to prevent image from disappearing
            qrcode_label.pack()
        except FileNotFoundError:
            ttk.Label(
                qrcode_frame, 
                text=f"{payment_method} QR code image not found\nPlease ensure {image_path} exists", 
                foreground="red", 
                font=("Arial", 10),
                justify=tk.CENTER
            ).pack(pady=50)
        except Exception as e:
            ttk.Label(
                qrcode_frame, 
                text=f"Image loading error: {str(e)}", 
                foreground="red",
                justify=tk.CENTER
            ).pack(pady=50)

        # 3. Payment confirmation logic
        def confirm_payment():
            try:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # Update status of all related orders
                for order in orders:
                    order_id = order['id']
                    self.cursor.execute("""
                        UPDATE orders SET 
                            status = 'Paid',
                            checkout_time = ?,
                            payment_method = ?,
                            total_amount = ?,
                            received_amount = ?,
                            change_amount = 0
                        WHERE id = ?
                    """, (current_time, payment_method, total_amount, total_amount, order_id))
                
                self.connection.commit()
                messagebox.showinfo(
                    "Success", 
                    f"{payment_method} payment successful!\nTransaction amount: ¥{total_amount:.2f}"
                )
                
                self.print_receipt(
                orders=orders,
                total_amount=total_amount,
                payment_method=payment_method,
                checkout_time=current_time,
                received=total_amount,  # WeChat/Alipay payment amount equals receivable amount
                change=0  # No change
                )
                
                pay_window.destroy()  # Close payment window
                
                # Refresh interface data
                self.refresh_order_display()
                self.refresh_tables()
                
            except Exception as e:
                self.connection.rollback()
                messagebox.showerror("Error", f"Payment processing failed: {str(e)}")

        # 4. Bottom buttons
        btn_frame = ttk.Frame(pay_window)
        btn_frame.pack(pady=30)
        
        ttk.Button(
            btn_frame, 
            text="Confirm Payment", 
            width=20,
            command=confirm_payment
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            btn_frame, 
            text="Cancel", 
            command=pay_window.destroy
        ).pack(side=tk.LEFT, padx=10)

    def process_cash_payment(self, dialog, orders, total_amount, table_id):
        """Process cash payment"""
        dialog.destroy()
        
        # Create cash payment window
        cash_dialog = tk.Toplevel(self.root)
        cash_dialog.title("Cash Payment")
        cash_dialog.geometry("300x200")
        cash_dialog.resizable(False, False)
        cash_dialog.transient(self.root)
        cash_dialog.grab_set()

        # Display amount due
        ttk.Label(cash_dialog, text=f"Amount Due: ¥{total_amount:.2f}", font=("Arial", 10)).pack(pady=5)
        
        # Received amount input
        ttk.Label(cash_dialog, text="Please enter received amount:").pack(pady=5)
        
        amount_frame = ttk.Frame(cash_dialog)
        amount_frame.pack(pady=5)
        
        received_var = tk.StringVar()
        received_entry = ttk.Entry(amount_frame, textvariable=received_var, width=15, font=("Arial", 12))
        received_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(amount_frame, text="CNY").pack(side=tk.LEFT)
        
        # Change amount display
        change_var = tk.StringVar(value="Change: ¥0.00")
        ttk.Label(cash_dialog, textvariable=change_var).pack(pady=10)
        
        # Calculate change in real-time
        def calculate_change(*args):
            try:
                received = float(received_var.get())
                change = received - total_amount
                if change >= 0:
                    change_var.set(f"Change: ¥{change:.2f}")
                else:
                    change_var.set(f"Insufficient amount, short by: ¥{abs(change):.2f}")
            except ValueError:
                change_var.set("Please enter a valid amount")

        received_var.trace_add("write", calculate_change)

        # Confirm payment button
        def confirm_cash_payment():
            try:
                received_amount = float(received_var.get())
                if received_amount < total_amount:
                    messagebox.showwarning("Warning", "Insufficient received amount!")
                    return
                    
                change_amount = received_amount - total_amount
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Update order status
                for order in orders:
                    order_id = order['id']
                    self.cursor.execute("""
                        UPDATE orders SET 
                            status = 'Paid',
                            checkout_time = ?,
                            payment_method = 'Cash Payment',
                            received_amount = ?,
                            change_amount = ?
                        WHERE id = ?
                    """, (current_time, received_amount, change_amount, order_id))

                # Update table status to Free
                self.cursor.execute("UPDATE tables SET status = 'Free' WHERE id = ?", (table_id,))
                
                self.connection.commit()
                messagebox.showinfo("Success", 
                    f"Cash payment successful!\nAmount Due: ¥{total_amount:.2f}\n"
                    f"Received: ¥{received_amount:.2f}\nChange: ¥{change_amount:.2f}")
                
                self.print_receipt(
                    orders=orders,
                    total_amount=total_amount,
                    payment_method="Cash Payment",
                    checkout_time=current_time,
                    received=received_amount,
                    change=change_amount
                )

                cash_dialog.destroy()
                
                # Refresh interface
                self.refresh_order_display()
                self.refresh_tables()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
            except Exception as e:
                self.connection.rollback()
                messagebox.showerror("Error", f"Payment processing failed: {str(e)}")

        btn_frame = ttk.Frame(cash_dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Confirm Receipt", command=confirm_cash_payment).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=cash_dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        # Auto-focus on input field
        received_entry.focus_set()

    def build_receipt(self, table_number, orders, payment_method, received, change, checkout_time):
        """Build receipt content"""
        receipt = []
        receipt.append("="*40)
        receipt.append("          Restaurant Receipt          ")
        receipt.append("="*40)
        receipt.append(f"Table Number: {table_number}")
        receipt.append(f"Checkout Time: {checkout_time}")
        receipt.append("-"*40)
        receipt.append(f"{'Item Name':<18} {'Qty':<6} {'Price':<8} {'Subtotal':<8}")
        receipt.append("-"*40)
        
        total_amount = 0
        
        # Iterate through dishes of all orders
        for order in orders:
            order_id = order['id']
            self.cursor.execute("""
                SELECT d.name, oi.quantity, d.price, oi.subtotal 
                FROM order_items oi
                JOIN dishes d ON oi.dish_id = d.id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = self.cursor.fetchall()
            
            for item in items:
                name = item['name']
                quantity = item['quantity']
                price = item['price']
                subtotal = item['subtotal']
                total_amount += subtotal
                receipt.append(f"{name[:15]:<18} {quantity:<6} {price:.2f}CNY  {subtotal:.2f}CNY")
        
        receipt.append("-"*40)
        receipt.append(f"{'Total:':<32} {total_amount:.2f}CNY")
        receipt.append(f"Payment Method: {payment_method}")
        receipt.append(f"Received Amount: {received:.2f}CNY")
        receipt.append(f"Change: {change:.2f}CNY")
        receipt.append("="*40)
        receipt.append("Thank you for your patronage, come again soon!")
        
        return "\n".join(receipt)
    
    def print_receipt(self, orders, total_amount, payment_method, checkout_time, received=0, change=0):
        """Print receipt"""
        receipt = f"""
        =================================
                Restaurant Receipt
        =================================
        Checkout Time: {checkout_time}
        Table: {self.selected_table_var.get()}
        ---------------------------------
        """
        
        for order in orders:
            receipt += f"Order ID: {order['id']}\n"
            # Get order details
            self.cursor.execute("""
                SELECT d.name, oi.quantity, oi.subtotal
                FROM order_items oi
                JOIN dishes d ON oi.dish_id = d.id
                WHERE oi.order_id = ?
            """, (order['id'],))
            
            for item in self.cursor.fetchall():
                receipt += f"  {item['name']} ×{item['quantity']}  {item['subtotal']:.2f}CNY\n"
        
        receipt += f"""
        ---------------------------------
        Amount Due: {total_amount:.2f}CNY
        """
        
        # Display received amount and change for cash payment
        if payment_method == "Cash Payment":
            receipt += f"""
        Received Amount: {received:.2f}CNY
        Change Amount: {change:.2f}CNY
        """
        
        receipt += f"""
        Payment Method: {payment_method}
        =================================
              Thank you for coming!
        =================================
        """
        
        messagebox.showinfo("Print Receipt", receipt)

    # =========================================================================
    #  Kitchen Tab 
    # =========================================================================
    def create_kitchen_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Kitchen View")

        # Order Filtering Framework
        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(filter_frame, text="Filter by Status:").pack(side=tk.LEFT)
        self.kitchen_status_var = tk.StringVar(value="Pending")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.kitchen_status_var,
                                values=["All", "Pending", "In Progress","Served"], width=15)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_kitchen_orders())

        # Order List
        order_frame = ttk.LabelFrame(tab, text="Orders to Prepare")
        order_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # scroll bar
        kitchen_v_scroll = ttk.Scrollbar(order_frame, orient=tk.VERTICAL)
        kitchen_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        kitchen_h_scroll = ttk.Scrollbar(order_frame, orient=tk.HORIZONTAL)
        kitchen_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.kitchen_tree = ttk.Treeview(order_frame,
                                        columns=("order_id", "table_number", "dish", "quantity", "status", "order_time"),
                                        show="headings",
                                        yscrollcommand=kitchen_v_scroll.set,
                                        xscrollcommand=kitchen_h_scroll.set)
        kitchen_v_scroll.config(command=self.kitchen_tree.yview)
        kitchen_h_scroll.config(command=self.kitchen_tree.xview)

        # Set column headers
        self.kitchen_tree.heading("order_id", text="Order ID")
        self.kitchen_tree.heading("table_number", text="Table")
        self.kitchen_tree.heading("dish", text="Dish")
        self.kitchen_tree.heading("quantity", text="Quantity")
        self.kitchen_tree.heading("status", text="Status")
        self.kitchen_tree.heading("order_time", text="Order Time")

        self.kitchen_tree.pack(fill=tk.BOTH, expand=True)

        # Status update button
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Start Preparation", command=self.start_preparation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Mark as Served", command=self.mark_as_served).pack(side=tk.LEFT, padx=5)

        self.refresh_kitchen_orders()

    def refresh_kitchen_orders(self):
        """Refresh the kitchen order list, using status values that meet the constraints as query conditions."""
        for item in self.kitchen_tree.get_children():
            self.kitchen_tree.delete(item)
        
        status_filter = self.kitchen_status_var.get()
        query = """
            SELECT oi.id, o.id as order_id, t.table_number, d.name as dish, oi.quantity, oi.status, o.order_date
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN tables t ON o.table_id = t.id
            JOIN dishes d ON oi.dish_id = d.id
            WHERE 1=1
        """
        params = []
        
        # Filter criteria only use status values allowed by the database
        if status_filter != "All":
            query += " AND oi.status = ?"
            params.append(status_filter) 
        
        query += " ORDER BY o.order_date DESC, oi.id"
        self.cursor.execute(query, params)
        
        for row in self.cursor.fetchall():
            self.kitchen_tree.insert("", "end", values=(
                row['order_id'],
                row['table_number'],
                row['dish'],
                row['quantity'],
                row['status'],
                row['order_date']
            ), tags=(row['id'],))  

    def start_preparation(self):
        """Change the dish status to "In Progress" and deduct inventory"""
        selected = self.kitchen_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a dish to start preparation")
            return
        
        # Get the selected order item ID
        item_id = self.kitchen_tree.item(selected[0], "tags")[0]
        
        # Query order item details
        self.cursor.execute("""
            SELECT oi.dish_id, oi.quantity, oi.status, d.name
            FROM order_items oi
            JOIN dishes d ON oi.dish_id = d.id
            WHERE oi.id = ?
        """, (item_id,))
        
        item = self.cursor.fetchone()
        if not item:
            messagebox.showerror("Error", "Selected item not found")
            return
        
        # Check if the current status is Pending
        if item['status'] != 'Pending':
            messagebox.showwarning("Warning", "Only pending items can be started")
            return
        
        # Check and deduct inventory
        result = self.check_and_deduct_ingredients(
            dish_id=item['dish_id'],
            quantity=item['quantity'],
            deduct=True
        )
        
        if not result:
            messagebox.showerror("Inventory Error", "Failed to deduct ingredients. Check inventory status.")
            return
        
        # Update status after successful inventory deduction
        try:
            self.cursor.execute(
                "UPDATE order_items SET status = 'In Progress' WHERE id = ?",
                (item_id,)
            )
            self.connection.commit()
            messagebox.showinfo("Success", f"Started preparing {item['name']}")
            self.refresh_kitchen_orders()
            self.on_table_selected()  # Refresh order page display
        except Exception as e:
            self.connection.rollback()
            messagebox.showerror("Error", f"Failed to update status: {str(e)}")

    def mark_as_served(self):
        """Change the dish status to 'Completed' (order item) and synchronously update the order status to 'Served' (in compliance with the orders table constraints)"""
        selected = self.kitchen_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a dish to mark as completed")
            return
        
        item_id = self.kitchen_tree.item(selected[0], "tags")[0]
        
        # Check if the current status is In Progress (can only be changed from In Progress to Completed)
        self.cursor.execute("""
            SELECT status, d.name 
            FROM order_items oi 
            JOIN dishes d ON oi.dish_id = d.id 
            WHERE oi.id = ?
        """, (item_id,))
        item = self.cursor.fetchone()
        
        if not item:
            messagebox.showerror("Error", "Selected item not found")
            return
            
        if item['status'] != 'In Progress':
            messagebox.showwarning("Warning", "Only items in progress can be marked as completed")
            return
        
        try:
            # 1. Update the order item status to 'Completed' (assuming the order_items table constraints allow it)
            self.cursor.execute(
                "UPDATE order_items SET status = 'Completed' WHERE id = ?",
                (item_id,)
            )
            
            # 2. Get the order ID to which the current order item belongs
            self.cursor.execute("""
                SELECT o.id 
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE oi.id = ?
            """, (item_id,))
            order_id = self.cursor.fetchone()['id']
            
            # 3. Check if all dishes in this order have been completed
            self.cursor.execute("""
                SELECT COUNT(*) as remaining 
                FROM order_items 
                WHERE order_id = ? AND status != 'Completed'
            """, (order_id,))
            
            # 4. If all dishes are completed, update the order status to 'Served' (in compliance with the CHECK constraint in the orders table).
            if self.cursor.fetchone()['remaining'] == 0:
                self.cursor.execute("""
                    UPDATE orders 
                    SET status = 'Served' 
                    WHERE id = ?
                """, (order_id,))
            
            self.connection.commit()
            messagebox.showinfo("Success", f"{item['name']} marked as completed")
            self.refresh_kitchen_orders()
            self.on_table_selected()  # Refresh order page display
        except Exception as e:
            self.connection.rollback()
            messagebox.showerror("Error", f"Failed to update status: {str(e)}")

    def update_kitchen_item_status(self, event):
        """Double-click to directly switch the order item status: Pending → In Progress → Completed"""
        sel = self.kitchen_tree.selection()
        if not sel:
            return
        
        item = self.kitchen_tree.item(sel[0])
        item_id = item['values'][0]
        current_status = item['values'][4]
        
        # Define the state switching sequence
        status_sequence = {
            "Pending": "In Progress",
            "In Progress": "Completed",
            "Completed": "Completed"  # The status will not change once completed.
        }
        
        # Get new status
        new_status = status_sequence.get(current_status, current_status)
        
        # If the status remains unchanged, no action is required.
        if new_status == current_status:
            return
        
        # Update database
        try:
            self.cursor.execute(
                "UPDATE order_items SET status = ? WHERE id = ?",
                (new_status, item_id)
            )
            self.connection.commit()
            
            # If all items are completed, update the order status
            self.cursor.execute("SELECT order_id FROM order_items WHERE id = ?", (item_id,))
            order_id = self.cursor.fetchone()['order_id']
            
            self.cursor.execute("SELECT status FROM order_items WHERE order_id = ?", (order_id,))
            all_statuses = [row['status'] for row in self.cursor.fetchall()]
            
            if all(s == "Completed" for s in all_statuses):
                self.cursor.execute("UPDATE orders SET status = 'Served' WHERE id = ?", (order_id,))
                self.connection.commit()
            
            self.refresh_kitchen_orders()
            # Refresh the order management interface simultaneously
            self.on_table_selected()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update status: {str(e)}")

    def refresh_kitchen_view(self):
        """Refresh kitchen view (using database-allowed status values)"""
        for item in self.kitchen_tree.get_children():
            self.kitchen_tree.delete(item)
        
        self.cursor.execute("""
            SELECT oi.order_id, t.table_number, d.name, oi.status, o.order_date
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN tables t ON o.table_id = t.id
            JOIN dishes d ON oi.dish_id = d.id
            WHERE o.status IN ('In Progress', 'Served') 
            ORDER BY o.order_date DESC, oi.status
        """)
        
        for row in self.cursor.fetchall():
            self.kitchen_tree.insert("", "end", values=(
                row['order_id'],
                row['table_number'],
                row['name'],
                row['status'],
                row['order_date']
            ))
    # =========================================================================
    # Inventory Management Tab 
    # =========================================================================
    def create_inventory_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Inventory Management")

        # Buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Add Ingredient", command=self.add_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Ingredient", command=self.delete_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Inventory", command=self.update_ingredient).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh Inventory", command=self.refresh_inventory).pack(side=tk.LEFT, padx=5)
        
        # Inventory list (add scrollbars)
        inventory_container = ttk.Frame(tab)
        inventory_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create scrollbars
        v_scrollbar_inventory = ttk.Scrollbar(inventory_container, orient=tk.VERTICAL)
        v_scrollbar_inventory.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar_inventory = ttk.Scrollbar(inventory_container, orient=tk.HORIZONTAL)
        h_scrollbar_inventory.pack(side=tk.BOTTOM, fill=tk.X)

        self.inventory_tree = ttk.Treeview(
            inventory_container,
            columns=("id", "name", "unit", "stock", "low_stock_threshold", "status"),
            show="headings",
            yscrollcommand=v_scrollbar_inventory.set,
            xscrollcommand=h_scrollbar_inventory.set
        )
        
        # Configure scrollbars
        v_scrollbar_inventory.config(command=self.inventory_tree.yview)
        h_scrollbar_inventory.config(command=self.inventory_tree.xview)

        for col in ("id", "name", "unit", "stock", "low_stock_threshold", "status"):
            self.inventory_tree.heading(col, text=col)
        self.inventory_tree.pack(fill=tk.BOTH, expand=True)

        self.refresh_inventory()

    def refresh_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        self.cursor.execute("SELECT * FROM ingredients s")
        for row in self.cursor.fetchall():
            # Format stock to two decimal places
            formatted_stock = f"{row['stock']:.2f}"
            # Determine inventory status
            if row['stock'] <= row['low_stock_threshold']:
                status = "Need Restock"
            else:
                status = "Normal"
            self.inventory_tree.insert("", "end", values=(
                row['id'],
                row['name'],
                row['unit'],
                formatted_stock,  # Display two decimal places
                row['low_stock_threshold'],
                status  # Add status information
            ))

    def add_ingredient(self):
        name = simpledialog.askstring("Add Ingredient", "Ingredient Name:")
        if not name:
            return
            
        unit = simpledialog.askstring("Add Ingredient", "Unit of Measurement (e.g. kg, pcs):")
        if not unit:
            return
            
        try:
            stock = float(simpledialog.askstring("Add Ingredient", "Initial Stock:"))
            threshold = float(simpledialog.askstring("Add Ingredient", "Low Stock Threshold:"))
            
            self.cursor.execute("""
                INSERT INTO ingredients (name, unit, stock, low_stock_threshold)
                VALUES (?, ?, ?, ?)
            """, (name, unit, stock, threshold))
            
            self.connection.commit()
            self.refresh_inventory()
            messagebox.showinfo("Success", f"Ingredient '{name}' added successfully")
            
        except ValueError:
            messagebox.showerror("Error", "Stock and threshold must be numbers")
        except Exception as e:
            messagebox.showerror("Error", f"Add failed: {str(e)}")

    def delete_ingredient(self):
        sel = self.inventory_tree.selection()
        if not sel:
            messagebox.showwarning("Prompt", "Please select the ingredient to delete")
            return
            
        item = self.inventory_tree.item(sel[0])
        values = item["values"]
        if not values:
            return
            
        ingredient_id, name, unit, stock, threshold, status = values

        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name}'?")
        if not confirm:
            return

        try:
            self.cursor.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
            self.connection.commit()
            
            self.refresh_inventory()
            messagebox.showinfo("Success", f"Ingredient '{name}' has been deleted")
            
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed: {str(e)}")

    def update_ingredient(self):
        sel = self.inventory_tree.selection()
        if not sel:
            messagebox.showwarning("Prompt", "Please select the ingredient to update")
            return
            
        item = self.inventory_tree.item(sel[0])
        values = item["values"]
        if not values:
            return
            
        # Adjust variable count to match columns including status
        ingredient_id, name, unit, current_stock, threshold, status = values
        
        try:
            new_stock = float(simpledialog.askstring(
                "Update Inventory", 
                f"Current Stock: {current_stock} {unit}\nPlease enter new stock:",
                initialvalue=current_stock
            ))
            
            if new_stock < 0:
                messagebox.showerror("Error", "Stock cannot be negative")
                return
                
            self.cursor.execute(
                "UPDATE ingredients SET stock = ? WHERE id = ?",
                (new_stock, ingredient_id)
            )
            
            self.connection.commit()
            self.refresh_inventory()
            messagebox.showinfo("Success", f"Ingredient '{name}' stock has been updated")
            
        except ValueError:
            messagebox.showerror("Error", "Stock must be a number")
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantApp(root)
    root.mainloop()
