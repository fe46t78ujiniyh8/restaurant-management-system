# restaurant-management-system
SDSC 5003 Project Track1

Restaurant Management System

A desktop application for managing restaurant operations, built with Python and SQLite. This system helps streamline table management, order processing, kitchen coordination, and inventory tracking.

Features
Table Management: Add, delete, and update table status (Free/Occupied)
Order Management: Create orders, add dishes, submit orders, and process checkout
Inventory Tracking: Monitor ingredient stock levels and automatically deduct inventory when orders are placed
Premade Dishes Support: Special handling for premade meal kits with dedicated inventory management
Database Integration: Uses SQLite for reliable local data storage with automatic table creation and sample data initialization

Tech Stack
Python 3.x
Tkinter (for GUI)
SQLite (for database)
Pillow (PIL) for image handling

Installation
Clone this repository:
git clone https://github.com/fe46t78ujiniyh8/restaurant-management-system.git
cd restaurant-management-system

Install required dependencies:
pip install pillow
(Tkinter and SQLite3 are usually included with standard Python installations)

Build DB:
restaurant_system.sql

Run the application:
python main.py

Usage

Table Management
Add Table: Click "Add Table" and enter table number and capacity
Delete Table: Select a table from the list and click "Delete Table"
Update Status: Double-click a table and select new status (1 for Free, 2 for Occupied)
Search/Filter: Use the search box and status filter to find specific tables

Order Management
Select a table from the dropdown menu
Click "Create Order" to start a new order for the selected table
Add dishes by double-clicking items in the "Dish List"
View current order details in the "Current Order" section
Use "Remove Dish" to remove items from the order
Click "Submit Order" to finalize the order
Process payment with "Checkout & Print" when the customer is ready

Inventory Management
The system automatically tracks ingredient stock levels. When orders are placed, it deducts the required ingredients from inventory and maintains logs of all inventory changes.

Database
The application uses a local SQLite database (restaurant_system.db) that is automatically created on first run. It includes sample data for:
Tables (5 sample tables with different capacities)
Dishes (5 Sichuan cuisine dishes and 4 premade dishes)
Ingredients (10 common ingredients and 4 premade meal kits)
Recipe associations between dishes and ingredients

Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
