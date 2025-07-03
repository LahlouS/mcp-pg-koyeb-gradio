import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import numpy as np
import time
import sys
# Load environment variables from .env file
env_file = '.env' if len(sys.argv) == 1 else sys.argv[1]
print(env_file)
load_dotenv(env_file)

# Fetch environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)

# Connect to the PostgreSQL database
def connect_to_db():
	try:
		connection = psycopg2.connect(
			dbname=DB_NAME,
			user=DB_USER,
			password=DB_PASSWORD,
			host=DB_HOST,
			port=DB_PORT
		)
		connection.autocommit = True
		return connection
	except Exception as e:
		print(f"Error connecting to the database: {e}")
		exit(1)

def get_table_columns(conn, table_name):
	cursor = conn.cursor()
	cursor.execute(
		"SELECT column_name FROM information_schema.columns WHERE table_name = %s;",
		(table_name,)
	)
	columns = [row[0] for row in cursor.fetchall()]
	cursor.close()
	return columns

def load_customers(path):
	df = pd.read_csv(path)

	# Convert Active: 1.0 => True, NaN => False
	df['active'] = df['Active'].apply(lambda x: True if x == 1.0 else False)
	df.drop(columns=['Active'], inplace=True)

	# Rename FN to fn (optional - if your schema uses lowercase)
	df.rename(columns={'FN': 'fn'}, inplace=True)

	# Replace NaN ages with 0 and cast to int
	df['age'] = df['age'].fillna(0).astype(int)

	return df



def load_articles(path):
	return pd.read_csv(path)

def load_transactions(path):
	df = pd.read_csv(path, parse_dates=['t_dat'])
	df.rename(columns={'t_dat': 'transaction_date'}, inplace=True)
	return df

def no_duplicate_in(df, var):
	return len(df[df[var].duplicated(keep=False)]) == 0

def check_columns_in_df(df, columns):
	missing_columns = [col for col in columns if col not in df.columns]
	if missing_columns:
		print(f"Missing columns: {missing_columns}")
		return False
	return True

def insert_df_to_db(df, conn, table_name, batch_size=1000):
	cursor = conn.cursor()
	table_columns = get_table_columns(conn, table_name)

	# Ensure column order and compatibility
	df_filtered = df.loc[:, [col for col in table_columns if col in df.columns]]
	
	if df_filtered.empty:
		print("No matching columns found or dataframe is empty")
		cursor.close()
		return

	columns = ', '.join(df_filtered.columns)
	placeholders = ', '.join(['%s'] * len(df_filtered.columns))
	insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

	total_rows = len(df_filtered)
	inserted_rows = 0
	skipped_rows = 0
	start_time = time.time()
	last_progress_time = start_time

	# Convert dataframe to list of tuples for batch processing
	data_tuples = [tuple(row) for row in df_filtered.values]
	
	# Process in batches
	for i in range(0, len(data_tuples), batch_size):
		batch = data_tuples[i:i + batch_size]
		
		try:
			cursor.executemany(insert_sql, batch)
			inserted_rows += len(batch)
			
		except psycopg2.IntegrityError as e:
			# If batch fails due to integrity error, try individual inserts for this batch
			print(f"Batch insert failed, trying individual inserts for batch starting at row {i}: {e}")
			conn.rollback()
			
			for j, row_data in enumerate(batch):
				try:
					cursor.execute(insert_sql, row_data)
					inserted_rows += 1
				except psycopg2.IntegrityError as row_e:
					print(f"Skipping row {i + j} due to IntegrityError: {row_e}")
					skipped_rows += 1
					conn.rollback()
					continue
				except Exception as row_e:
					print(f"Error inserting row {i + j}: {row_e}")
					skipped_rows += 1
					conn.rollback()
					continue
					
		except Exception as e:
			print(f"Error with batch starting at row {i}: {e}")
			conn.rollback()
			skipped_rows += len(batch)
			continue

		# Show progress every 5 seconds
		current_time = time.time()
		if current_time - last_progress_time >= 5:
			progress = ((i + len(batch)) / total_rows) * 100
			elapsed = current_time - start_time
			rate = inserted_rows / elapsed if elapsed > 0 else 0
			print(f"Progress: {progress:.2f}% ({inserted_rows}/{total_rows} inserted, {skipped_rows} skipped) - {rate:.0f} rows/sec")
			last_progress_time = current_time

	conn.commit()
	cursor.close()
	
	final_time = time.time() - start_time
	final_rate = inserted_rows / final_time if final_time > 0 else 0
	print(f"Complete: {inserted_rows}/{total_rows} rows inserted, {skipped_rows} skipped in {final_time:.2f}s ({final_rate:.0f} rows/sec)")

if __name__ == "__main__":
	try:
		customers_df = load_customers('./customers_filtered.csv')
		articles_df = load_articles('./articles_filtered.csv')
		transactions_df = load_transactions('./transaction_sample_3.csv')

		# assert no_duplicate_in(customers_df, 'customer_id'), "Duplicate customer_id detected"
		# assert no_duplicate_in(articles_df, 'article_id'), "Duplicate article_id detected"

		connection = connect_to_db()

		for df, table in [
			(customers_df, "customers"),
			(articles_df, "articles"),
			(transactions_df, "transactions")
		]:
			expected_columns = get_table_columns(connection, table)
			assert check_columns_in_df(df, expected_columns), f"DataFrame columns do not match for table {table}"
			print(f"Starting to insert into {table} ({len(df)} rows)...")
			insert_df_to_db(df, connection, table)

		print("DONE")

	except Exception as e:
		print(f"Migration failed: {e}")
