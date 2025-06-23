
server_instruct = """
	## Purpose
			This MCP server provides comprehensive e-commerce database analytics capabilities, enabling clients to explore database schemas, run queries, perform statistical analysis, and generate AI-powered insights. The server is designed to help users analyze customer behavior, sales patterns, and business metrics from e-commerce data.
					
			## 🎯 Use Cases
			This MCP server is designed for:
			- **E-commerce Analytics**: Customer behavior, sales patterns, product performance
			- **Business Intelligence**: KPI tracking, trend analysis, forecasting
			- **Statistical Research**: Hypothesis testing, comparative analysis
			- **Data Exploration**: Schema discovery, data profiling, relationship analysis
					
			## 📊 Database Schema & Discovery Functions
			### `get_schemas()`**Purpose**: Retrieve all database schemas
			### `get_db_infos()` **Purpose**: Get comprehensive database information and metadata
			### `get_list_of_tables_in_schema(schema_name: str)` **Purpose**: List all tables within a specific schema
			### `get_list_of_column_in_table(schema_name: str, table_name: str)` **Purpose**: Get detailed column information for a specific table

			## 🔍 Query & Data Manipulation Functions
			### `run_read_only_query(query: str)` **Purpose**: Execute read-only SQL queries safely

			## 📈 Statistical Analysis Functions
			### `do_annova(table_name: str, min_sample_size: int = 0)` **Purpose**: Perform ANOVA (Analysis of Variance) statistical test- **Use Case**: Testing if there are significant differences between group means
			### `do_tukey_test(table_name: str, min_sample_size: int = 0)` **Purpose**: Perform Tukey's HSD post-hoc analysis after ANOVA **Use Case**: Identifying which specific groups differ significantly **Prerequisite**: Should be used after significant ANOVA results

			## 🔄 Recommended Workflows
			### 1. Discovery Workflow
			get_schemas() → Discover available schemas
			get_list_of_tables_in_schema("public") → Find tables
			get_list_of_column_in_table("public", "customers") → Understand structure
			run_read_only_query("SELECT * FROM customers LIMIT 5") → Sample data

			### 2. Analysis Workflow
			run_read_only_query() → Explore data
			create_table_from_query() → Create analysis datasets
			do_annova() → Statistical testing
			do_tukey_test() → Post-hoc analysis
			generate_graph_wrapper() → Visualize results
								 
			## ✅ Best Practices for MCP Clients
			1. **Start with Discovery**: Always begin by exploring schemas and tables before analysis
			2. **Use Read-Only Queries**: Prefer `run_read_only_query()` for exploration to maintain data safety
			3. **Statistical Validation**: Use `do_annova()` before `do_tukey_test()` for proper statistical workflow
			5. **Clean Up**: Use `drop_table()` to remove temporary analysis tables when done
			6. **Error Handling**: All functions return status indicators - check for errors before proceeding
			7. **Data Safety**: Core tables (transactions, customers, articles) are protected from modification"""