import mysql.connector
from mysql.connector import Error

def check_database():
    try:
        # Koneksi ke database
        connection = mysql.connector.connect(
            host='localhost',
            database='heroin_db',
            user='root',
            password='sql123'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ Koneksi database berhasil!")
            
            # Check apakah tabel hypothesis ada dan berisi data
            cursor.execute("SELECT COUNT(*) FROM hypothesis")
            hypothesis_count = cursor.fetchone()[0]
            print(f"📊 Jumlah data hypothesis: {hypothesis_count}")
            
            if hypothesis_count > 0:
                cursor.execute("SELECT id, code, name, description FROM hypothesis")
                hypotheses = cursor.fetchall()
                print("\n📋 Data Hypothesis:")
                for h in hypotheses:
                    print(f"   ID: {h[0]}, Code: {h[1]}, Name: {h[2]}")
            else:
                print("⚠️  Tabel hypothesis kosong! Jalankan migrations.sql")
            
            # Check tabel lainnya
            tables_to_check = ['symptom', 'question', 'rule', 'user']
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"📊 Jumlah data {table}: {count}")
                except Error as e:
                    print(f"❌ Error checking table {table}: {e}")
            
            # Test query yang digunakan oleh aplikasi
            print("\n🔍 Testing API queries...")
            cursor.execute("SELECT id, code, name, description, cf_threshold_min, cf_threshold_max FROM hypothesis")
            api_data = cursor.fetchall()
            print(f"✅ Query API hypothesis berhasil: {len(api_data)} records")
            
            return True
            
    except Error as e:
        print(f"❌ Error koneksi database: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Pastikan MySQL server berjalan")
        print("2. Periksa username/password database")
        print("3. Pastikan database 'heroin_db' sudah dibuat")
        print("4. Jalankan migrations.sql untuk membuat tabel dan data")
        return False
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def test_flask_connection():
    """Test koneksi seperti yang digunakan Flask"""
    try:
        from sqlalchemy import create_engine, text
        
        # Gunakan connection string yang sama dengan Flask
        engine = create_engine('mysql://root:sql123@localhost/heroin_db')
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM hypothesis"))
            count = result.fetchone()[0]
            print(f"✅ Flask-style connection test: {count} hypotheses found")
            return True
            
    except Exception as e:
        print(f"❌ Flask-style connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Checking HEROin Database...\n")
    
    db_ok = check_database()
    flask_ok = test_flask_connection()
    
    if db_ok and flask_ok:
        print("\n✅ Database setup is OK! Your app should work.")
    else:
        print("\n❌ Database issues found. Please fix before running the app.")
        print("\n📝 Quick fix commands:")
        print("1. mysql -u root -p")
        print("2. CREATE DATABASE IF NOT EXISTS heroin_db;")
        print("3. USE heroin_db;")
        print("4. source migrations.sql;")