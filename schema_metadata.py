table_metadata = {
    "brands": """
    Stores brand information for bicycles.
    Columns:
    - brand_id (Integer): Primary Key. Unique identifier for the brand.
    - brand_name (Text): Name of the brand (e.g., Trek, Electra).
    """,
    
    "categories": """
    Stores category information for bicycles (e.g., Road, Mountain).
    Columns:
    - category_id (Integer): Primary Key. Unique identifier for the category.
    - category_name (Text): Name of the category.
    """,
    
    "products": """
    Stores product information including price and model year.
    Columns:
    - product_id (Integer): Primary Key.
    - product_name (Text): Name of the bicycle.
    - brand_id (Integer): Foreign Key referencing brands.
    - category_id (Integer): Foreign Key referencing categories.
    - model_year (Integer): The year the model was released.
    - list_price (Decimal): The listing price of the product.
    """,
    
    "customers": """
    Stores customer personal and contact information.
    Columns:
    - customer_id (Integer): Primary Key.
    - first_name (Text): Customer's first name.
    - last_name (Text): Customer's last name.
    - phone (Text): Phone number.
    - email (Text): Email address.
    - street, city, state, zip_code (Text): Address details.
    """,
    
    "orders": """
    Stores sales order headers.
    Columns:
    - order_id (Integer): Primary Key.
    - customer_id (Integer): Foreign Key referencing customers.
    - order_status (Integer): Status of the order (1=Pending, 2=Processing, 3=Rejected, 4=Completed).
    - order_date (Date): When the order was placed.
    - required_date (Date): When the order is required.
    - shipped_date (Date): When the order was shipped.
    - store_id (Integer): Foreign Key referencing stores.
    - staff_id (Integer): Foreign Key referencing staffs who processed the order.
    """,
    
    "order_items": """
    Stores line items for each order.
    Columns:
    - order_id (Integer): Foreign Key referencing orders.
    - item_id (Integer): Line item number.
    - product_id (Integer): Foreign Key referencing products.
    - quantity (Integer): Quantity ordered.
    - list_price (Decimal): Price per unit at time of order.
    - discount (Decimal): Discount applied (0.0 to 1.0).
    
    IMPORTANT REVENUE CALCULATION:
    - The 'list_price' is the starting price.
    - 'discount' is a decimal (e.g., 0.20 for 20%).
    - Realized Revenue per item = quantity * list_price * (1 - discount)
    - DO NOT just multiply quantity * list_price. You MUST subtract the discount.
    """,
    
    "stocks": """
    Stores inventory levels for products at specific stores.
    Columns:
    - store_id (Integer): Foreign Key referencing stores.
    - product_id (Integer): Foreign Key referencing products.
    - quantity (Integer): Number of units in stock.
    """,
    
    "stores": """
    Stores information about physical store locations.
    Columns:
    - store_id (Integer): Primary Key.
    - store_name (Text): Name of the store.
    - phone, email (Text): Contact info.
    - street, city, state, zip_code (Text): Address.
    """,
    
    "staffs": """
    Stores employee information.
    Columns:
    - staff_id (Integer): Primary Key.
    - first_name, last_name (Text): Name.
    - email, phone (Text): Contact.
    - active (Integer): 1 = Active, 0 = Inactive.
    - store_id (Integer): Store where staff works.
    - manager_id (Integer): Self-referencing FK to staffs (who is their manager).
    """
}
