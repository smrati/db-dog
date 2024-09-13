import os

# Get database connection details from environment variables
db_username = os.getenv('DB_USERNAME', 'admin_test_db')
db_password = os.getenv('DB_PASSWORD', 'admin123')
db_host = os.getenv('DB_HOST', '0.0.0.0')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'lms')
default_schema = os.getenv('DEFAULT_SCHEMA', 'public')