import gradio as gr
from database_connector import DatabaseInterface
from server_instruct import server_instruct
import var_stats

# Global state for database connection
db_interface = None
db_connection_status = "❌ Not Connected"

from database_connector import DatabaseInterface

def setup_database_connection(host: str, port: str, database: str, user: str, password: str):
	"""Setup database connection with user-provided configuration"""
	global db_interface, db_connection_status
	
	if not all([host.strip(), port.strip(), database.strip(), user.strip(), password.strip()]):
		db_connection_status = "❌ All fields are required"
		return db_connection_status, False
	
	try:
		db_config = {
			'host': host.strip(),
			'port': int(port.strip()),
			'database': database.strip(),
			'user': user.strip(),
			'password': password.strip()
		}
		
		# Test connection
		test_interface = DatabaseInterface(db_config)
		test_connection = test_interface.get_db_connection()
		test_connection.close()
		
		# If successful, set global interface
		db_interface = test_interface
		db_connection_status = f"✅ Connected to {database} at {host}:{port}"
		return db_connection_status, True
		
	except ValueError:
		db_connection_status = "❌ Port must be a valid number"
		return db_connection_status, False
	except Exception as e:
		db_connection_status = f"❌ Connection failed: {str(e)}"
		return db_connection_status, False

def handle_connection(host: str, port: int, database, user, password):
	"""
		this function allow you to connect to the Database using the provided credentials:
		the paramters are the following:
		Args:
			host (str): the given address.
			port (int): the connection port
			database (str): the name of the database
			user (str): the user
			password (str): the password
	
	"""
	status, success = setup_database_connection(host, port, database, user, password)
	return status

def get_connection_status():
	"""Get current database connection status"""
	return db_connection_status

def check_db_connection():
	"""Check if database is connected before operations"""
	if db_interface is None:
		return False, "❌ Please configure database connection first"
	return True, "✅ Database connected"

def get_db_infos():
	"""### `get_db_infos()`
	-> database name and description
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_database_info()

def get_schemas():
	"""### `get_schemas()`
	-> list availables schemas in the database
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_schemas()

def get_list_of_tables_in_schema(schema:str):
	"""### `get_list_of_tables_in_schema(schema_name: str)`
	Args:
		schema (str): the schema you want to discover tables for.
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_tables_in_schema(schema)

def get_availables_extensions():
	"""
	### `get_availables_extensions()`
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_extensions()

def get_list_of_column_in_table(schema, table):
	"""### `get_list_of_column_in_table(schema_name: str, table_name: str)`
		Args:
			schema (str): the schema you want to discover tables for.
			table (str): the table you want to discover colunms for.
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.list_columns_in_table(schema, table)

def run_read_only_query(query: str):
	"""### `run_read_only_query(query: str)`
		Args:
			query (str): read-only query that will be executed
		You will get the raw result following this pattern
		[(row_1_col_a, ..., row_1_col_b), (row_2_col_a, ..., row_2_col_b), ...]
		Or the sql error message if the query you wrote is not valid 
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.read_only_query(query)

def create_table_from_query(table_name: str, source_query: str):
	"""### `create_table_from_query(table_name: str, source_query: str)`
	this function is a tool for you to create intermediary table based on query on the database.
	this allow you to deepen your analysis for intricated request from the user.

	Args:
		table_name (str): the name of the table you want to create (must not overlap with existing tables)
		source_query (str): the SQL query that will be used to create the new table on like this: CREATE TABLE {table_name} AS {source_query}"

	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.create_table_from_query(table_name, source_query)

def drop_table(table_name: str):
	"""### `drop_table(table_name: str)`
		this function is to drop intermediary tables when user ask you to do or if you created a temporary table only to support further analysis 
		and the analysis is done
		Args:
			table_name (str): the name of the table you want to drop
	"""
	connected, status = check_db_connection()
	if not connected:
		return status
	return db_interface.drop_table(table_name)

def do_annova(table_name, min_sample_size=0):
	'''
		this function runs the annova on the dataset and render the associated F_score and p_value
		Args:
			table_name (str): the name of the table on which you want to run the ANOVA
			min_sample_size (int): default = 0, is used to exclude categories that does not have enough measurement.
		the selected table MUST have the following signature:

		groups | measurement

		exemple with the product_type_age table:

		type | age
		----------
		'Coat', '36'
		'Coat', '36'
		'Hat/beanie', '32'
		...

		min_sample_size is used to exclude categories that does not have enough measurement.
		default = 0: all categories are selected

		return type is: dict
		{
			"F-statistic": round(f_stat, 3),
			"p-value": round(p_value, 3)
		}
	'''
	return var_stats.anova(db_interface, table_name=table_name, min_sample_size=int(min_sample_size))

def do_tukey_test(table_name, min_sample_size=0):
	'''
		this function runs a Tukey's HSD (Honestly Significant Difference) test — a post-hoc analysis following ANOVA. 
		It tells you which specific pairs of groups differ significantly in their means
		IT is meant to be used after you run a successful anova and you obtain sgnificant F-satatistics and p-value
		table_name is the name of the table on which you want to run the ANOVA
		the selected table MUST have the following signature:

		groups | measurement

		exemple with the product_type_age table:

		type | age
		----------
		'Coat', 36
		'Coat', 36
		'Hat/beanie', 32
		...

		min_sample_size is used to exclude categories that does not have enough measurement.
		default = 0: all categories are selected

		the return result is the raw dataframe that correspond to the pair wize categorie that reject the hypothesis of non statistically difference between two group
		the signature of the dataframe is the following:
		group1 | group2 | meandiff p-adj | lower | upper | reject (only true)
	
	'''
	return var_stats.tukey_test(db_interface, table_name=table_name, min_sample_size=int(min_sample_size))

def do_tsne_embedding(query):
	"""

		this tool allow to run a TSNE dimensionality reduction algorythme and a clustering (HDBSCAN) on top of that.

		the input query, is a sql query that MUST return a table with at least the item id and the corresponding embeddding.
		FOR COMPUTATIONAL PURPOSE, THE QUERY YOU SEND MUST NOT RETURN A TABLE GREATER THAN 500 OUTPUT ROWS
		exemple:
		result = db_connection.read_only_query(query)
		result shape:
		article_id | embedding
		0125456    | [0.3, 0.5 ...]

		the return is a dictionnary that has the following format:

			return {
				"ids": ids,
				"x_axis": tsne_projection_x_list,
				"y_axis": tsne_projection_y_list,
				"labels": labels
			}
	"""

	return var_stats.embedding_clustering(db_interface, query)

def do_vector_centroid(query):
	"""
		this tool allow you to compute the centroid of a list of embedding vectors
		the input query, is a sql query that MUST return a table with only 1 column, the embeddings.
		exemple:
		result = db_connection.read_only_query(query)
		result shape:
		 embedding
		 [0.3, 0.5 ...]

		the return value is the computed centroid vector, that you can use to work with.
	"""
	return var_stats.vector_centroid(db_interface, query)

def get_mcp_server_instructions():
	"""
	Returns comprehensive usage guidelines and documentation for all MCP server functions.
	Call this function first to understand available tools, workflows, and best practices.
	
	This function provides:
	- Complete function documentation
	- Recommended workflows  
	- Best practices for MCP clients
	- Database schema information
	- Statistical analysis guidelines
	"""
	return server_instruct

# TAB 1: Database Configuration
with gr.Blocks(title="Database Configuration") as tab1:
	gr.Markdown("# 🔌 Database Configuration")
	gr.Markdown("*Configure your database connection before using the analytics platform*")
	
	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 🗄️ Database Connection")
			host_input = gr.Textbox(label="Host", placeholder="database.example.com", value="")
			port_input = gr.Textbox(label="Port", placeholder="5432", value="")
			database_input = gr.Textbox(label="Database", placeholder="my_database", value="")
			user_input = gr.Textbox(label="User", placeholder="db_user", value="")
			password_input = gr.Textbox(label="Password", type="password", placeholder="••••••••", value="")
			
			connect_btn = gr.Button("🔌 Connect to Database", variant="primary")
			
		with gr.Column(scale=1):
			connection_status = gr.Textbox(label="🔌 Connection Status", value=db_connection_status, interactive=False)
			gr.Markdown("### ℹ️ Instructions")
			gr.Markdown("""
			1. **Fill in your database credentials**
			2. **Click 'Connect to Database'**
			3. **Wait for successful connection**
			4. **Proceed to other tabs once connected**
			
			**Note**: All database operations require a valid connection.
			""")
	
	connect_btn.click(
		handle_connection,
		inputs=[host_input, port_input, database_input, user_input, password_input],
		outputs=connection_status
	)

# TAB 2: Database Operations
with gr.Blocks(title="Database Operations") as tab2:
	gr.Markdown("# 🗄️ Database Operations")
	gr.Markdown("*Explore database schema, tables, and run queries*")
	
	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 🗄️ Database Schema")
			discover_btn = gr.Button("📋 Get Schemas", variant="primary")
			database_info_btn = gr.Button("ℹ️ Get Database Info", variant="secondary")
			get_extension_btn = gr.Button("ℹ️ Get Database Extensions", variant="secondary")
		with gr.Column(scale=2):
			schema_info = gr.Textbox(label="📋 Schema Information", lines=5)
			db_info = gr.Textbox(label="ℹ️ Database Information", lines=5)
			db_extensions = gr.Textbox(label="ℹ️ Database Extensions", lines=5)
	
	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 📊 Table Explorer")
			table_in_schema_input = gr.Textbox(label="Schema Name", placeholder="public")
			table_in_schema_btn = gr.Button("Get Tables")

		with gr.Column(scale=2):
			table_in_schema = gr.Textbox(label="📊 Tables in Schema", lines=5)

	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 📄 Column Explorer")
			schema_input = gr.Textbox(label="Schema Name", placeholder="public")
			table_input = gr.Textbox(label="Table Name", placeholder="customers")
			column_btn = gr.Button("Get Columns")

		with gr.Column(scale=2):
			column_output = gr.Textbox(label="📄 Table Columns", lines=5)

	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 🔍 SQL Query")
			query_input = gr.Textbox(label="SQL Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
			query_btn = gr.Button("Execute Query", variant="primary")

		with gr.Column(scale=2):
			query_output = gr.Textbox(label="🔍 Query Results", lines=8)

	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 🔍 Create Table")
			table_name_input = gr.Textbox(label="Table Name", placeholder="table")
			source_query_input = gr.Textbox(label="Source Query", lines=3, placeholder="SELECT * FROM customers LIMIT 10")
			create_table_from_query_btn = gr.Button("Create Table", variant="primary")

		with gr.Column(scale=2):
			table_status = gr.Textbox(label="table status")

	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### 🔍 Drop Table")
			drop_table_name_input = gr.Textbox(label="Table Name", placeholder="table")
			drop_table_btn = gr.Button("Drop Table", variant="primary")
			
		with gr.Column(scale=2):
			drop_table_status = gr.Textbox(label="drop table status")
	
	# Event handlers for Tab 1
	discover_btn.click(get_schemas, outputs=schema_info)
	database_info_btn.click(get_db_infos, outputs=db_info)
	get_extension_btn.click(get_availables_extensions, outputs=db_extensions)
	table_in_schema_btn.click(get_list_of_tables_in_schema, inputs=table_in_schema_input, outputs=table_in_schema)
	column_btn.click(get_list_of_column_in_table, inputs=[schema_input, table_input], outputs=column_output)
	query_btn.click(run_read_only_query, inputs=query_input, outputs=query_output)
	create_table_from_query_btn.click(create_table_from_query, inputs=[table_name_input, source_query_input], outputs=table_status)
	drop_table_btn.click(drop_table, inputs=drop_table_name_input, outputs=drop_table_status)

# TAB 3: Some more "fancy", Statistics
with gr.Blocks(title="Statistical Analysis") as tab3:
	gr.Markdown("# 📊 Statistical Analysis")
	gr.Markdown("*Run statistical tests on your data*")

	with gr.Row():
		with gr.Column(scale=1):
			gr.Markdown("### enter a dict that comply with the annova function")
			annova_input = gr.Textbox(label="annova")
			annova_min_sample_input = gr.Textbox(label="min sample size for annova")
			annova_btn = gr.Button("run annova")

			gr.Markdown("### enter a table that comply for tukey function")
			tukey_input = gr.Textbox(label="tukey")
			tukey_min_sample_input = gr.Textbox(label="min sample size for tukey")
			tukey_btn = gr.Button("run tukey")

			gr.Markdown("### Enter a query that comply with the requested embedding format")
			tsne_cluster_input = gr.Textbox(label="embedding_table")
			tsne_cluster_btn = gr.Button("run TSNE")

			gr.Markdown("### Enter a query that comply with the requested embedding centroid format")
			vector_centroid_input = gr.Textbox(label="embedding_table_for_vector")
			vector_centroid_btn = gr.Button("Compute centroid")


		with gr.Column(scale=2):
			annova_output = gr.Textbox(label="annova output")
			tukey_output = gr.Textbox(label="tukey output")
			tsne_output = gr.Textbox(label="tsne_clustering output")
			vector_centroid_output = gr.Textbox(label="Centroid")
	
	# Database operations
	annova_btn.click(do_annova, inputs=[annova_input, annova_min_sample_input], outputs=annova_output)
	tukey_btn.click(do_tukey_test, inputs=[tukey_input, tukey_min_sample_input], outputs=tukey_output)
	tsne_cluster_btn.click(do_tsne_embedding, inputs=tsne_cluster_input, outputs=tsne_output)
	vector_centroid_btn.click(do_vector_centroid, inputs=vector_centroid_input, outputs=vector_centroid_output)

with gr.Blocks(title="MCP guidelines") as tab4:
	gr.Markdown("### 📚 Server Documentation & guidelines")
	instructions_btn = gr.Button("📖 Get MCP Instructions", variant="secondary")
	instructions_output = gr.Textbox(label="📚 MCP Server Instructions", lines=15)
	instructions_btn.click(get_mcp_server_instructions, outputs=instructions_output)

with gr.Blocks(title="Application Guide") as tab0:
	gr.Markdown("# Deploy MCP server to interact with your data super easily with Koyeb and Gradio")
	gr.Markdown("## 🎯 Gradio MCP Server for PostgreSQL: building an autonomous data analyst")
	

# Create the TabbedInterface
interface = gr.TabbedInterface(
	[tab0, tab1, tab2, tab3, tab4], 
	tab_names=["Welcome","🔌 Database Setup", "🗄️ Database Operations", "📊 Statistical Analysis", "📊 MCP client guidelines"],
	title="Postgres Database Analytics MCP Server",
	theme=gr.themes.Soft()
)

# Launch the app
if __name__ == "__main__":
	print("🚀 Starting Database Analytics MCP Server...")
	print(f"🌐 Dashboard: http://localhost:7860")
	
	interface.launch(server_name="0.0.0.0", server_port=8000, mcp_server=True)