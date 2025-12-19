
import pandas as pd

# Load data
stores_df = pd.read_csv('./bike-store-data/stores.csv')
orders_df = pd.read_csv('./bike-store-data/orders.csv')
items_df = pd.read_csv('./bike-store-data/order_items.csv')

# Filter for completed orders (Status 4 = Completed)
# Based on previous context, status 4 is completed.
completed_orders = orders_df[orders_df['order_status'] == 4]

# Calculate revenue per item
items_df['revenue'] = items_df['quantity'] * items_df['list_price'] * (1 - items_df['discount'])

# Sum revenue per order
order_revenue = items_df.groupby('order_id')['revenue'].sum().reset_index()

# Join orders with revenue
orders_with_revenue = pd.merge(completed_orders, order_revenue, on='order_id', how='inner')

# Group by store
store_revenue = orders_with_revenue.groupby('store_id')['revenue'].sum().reset_index()

# Join with store names
final_df = pd.merge(store_revenue, stores_df[['store_id', 'store_name']], on='store_id')

# Sort by revenue descending
final_df = final_df.sort_values('revenue', ascending=False)

# Format nicely
pd.options.display.float_format = '${:,.2f}'.format
print(final_df[['store_name', 'revenue']])
