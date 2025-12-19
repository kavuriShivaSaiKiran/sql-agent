
import pandas as pd

# Load necessary CSVs
stocks = pd.read_csv('bike-store-data/stocks.csv')
products = pd.read_csv('bike-store-data/products.csv')
categories = pd.read_csv('bike-store-data/categories.csv')
stores = pd.read_csv('bike-store-data/stores.csv')

# Filter for 'Mountain Bikes' category (checking actual category name)
mb_category = categories[categories['category_name'] == 'Mountain Bikes']
if mb_category.empty:
    print("Error: Category 'Mountain Bikes' not found.")
else:
    category_id = mb_category.iloc[0]['category_id']
    
    # Filter for 'Baldwin Bikes' store
    baldwin_store = stores[stores['store_name'] == 'Baldwin Bikes']
    if baldwin_store.empty:
        print("Error: Store 'Baldwin Bikes' not found.")
    else:
        store_id = baldwin_store.iloc[0]['store_id']
        
        # Get all product IDs for Mountain Bikes
        mb_products = products[products['category_id'] == category_id]
        mb_product_ids = mb_products['product_id'].tolist()
        
        # Filter stocks for these products at this store
        store_stocks = stocks[
            (stocks['store_id'] == store_id) & 
            (stocks['product_id'].isin(mb_product_ids))
        ]
        
        total_quantity = store_stocks['quantity'].sum()
        
        print(f"Total 'Mountain Bikes' in stock at 'Baldwin Bikes': {total_quantity}")
