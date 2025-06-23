import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import numpy as np
import time

# Load environment variables from .env file
load_dotenv()

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

def insert_df_to_db(df, conn, table_name):
	cursor = conn.cursor()
	table_columns = get_table_columns(conn, table_name)

	# Ensure column order and compatibility
	df_filtered = df.loc[:, [col for col in table_columns if col in df.columns]]

	columns = ', '.join(df_filtered.columns)
	values = ', '.join([f"%({col})s" for col in df_filtered.columns])
	insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

	total_rows = len(df_filtered)
	inserted_rows = 0
	start_time = time.time()

	for i, row in df_filtered.iterrows():
		try:
			cursor.execute(insert_sql, row.to_dict())
			inserted_rows += 1
		except psycopg2.IntegrityError as e:
			print(f"Skipping row due to IntegrityError: {e}")
			conn.rollback()
			continue
		except Exception as e:
			print(f"Error inserting row: {e}\n***\n", row.to_dict())
			conn.rollback()
			continue

		if time.time() - start_time >= 5:
			progress = (inserted_rows / total_rows) * 100
			print(f"Progress: {progress:.2f}% ({inserted_rows}/{total_rows})")
			start_time = time.time()

	conn.commit()
	cursor.close()

if __name__ == "__main__":
	try:
		customers_df = load_customers('./customers_df_filtered.csv')
		articles_df = load_articles('./articles.csv')
		transactions_df = load_transactions('./transaction_sample.csv')

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
