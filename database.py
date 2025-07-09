import mysql.connector
from mysql.connector import Error
from config import Config
from werkzeug.security import generate_password_hash

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def initialize_database():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        
        # Create users table
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            role ENUM('admin', 'registrar') DEFAULT 'registrar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create students table
        students_table = """
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(20) UNIQUE NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            date_of_birth DATE,
            gender ENUM('Male', 'Female', 'Other'),
            enrollment_date DATE NOT NULL,
            program VARCHAR(100),
            added_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (added_by) REFERENCES users(id)
        )
        """
        
        try:
            cursor.execute(users_table)
            cursor.execute(students_table)
            
            # Create admin user if not exists
            admin_password = generate_password_hash('admin123')
            cursor.execute("""
                INSERT IGNORE INTO users (username, email, password_hash, full_name, role)
                VALUES ('admin', 'admin@school.edu', %s, 'System Administrator', 'admin')
            """, (admin_password,))
            
            connection.commit()
            print("Database initialized successfully")
        except Error as e:
            print(f"Error initializing database: {e}")
        finally:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    initialize_database()