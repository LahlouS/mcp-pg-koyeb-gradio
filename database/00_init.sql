-- migration.sql (updated to reflect 'FN' as FLOAT)

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS customers;

-- Create the customers table
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    FN FLOAT,
    active BOOLEAN,
    club_member_status TEXT,
    fashion_news_frequency TEXT,
    age INTEGER,
    postal_code TEXT
);

-- Create the articles table
CREATE TABLE articles (
    article_id TEXT PRIMARY KEY,
    product_code TEXT,
    prod_name TEXT,
    product_type_no INTEGER,
    product_type_name TEXT,
    product_group_name TEXT,
    graphical_appearance_no INTEGER,
    graphical_appearance_name TEXT,
    colour_group_code TEXT,
    colour_group_name TEXT,
    perceived_colour_value_id INTEGER,
    perceived_colour_value_name TEXT,
    perceived_colour_master_id INTEGER,
    perceived_colour_master_name TEXT,
    department_no INTEGER,
    department_name TEXT,
    index_code TEXT,
    index_name TEXT,
    index_group_no INTEGER,
    index_group_name TEXT,
    section_no INTEGER,
    section_name TEXT,
    garment_group_no INTEGER,
    garment_group_name TEXT,
    detail_desc TEXT
);

-- Create the transactions table
CREATE TABLE transactions (
    transaction_date DATE,
    customer_id TEXT REFERENCES customers(customer_id),
    article_id TEXT REFERENCES articles(article_id),
    price NUMERIC(10, 6),
    sales_channel_id INTEGER
);

-- Optional: Indexes to speed up queries
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX idx_transactions_article_id ON transactions(article_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
