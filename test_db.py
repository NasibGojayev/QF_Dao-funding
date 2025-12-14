import psycopg2

print("Attempting to connect to Railway DB...")

try:
    # Establishing the connection
    connection = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="@HELLOWORLD202",
        host="db.gpsoosknwzkibkzgdxoh.supabase.co",
        port="5432"
    )

    # Create a cursor object
    cursor = connection.cursor()

    # Execute a simple query to check the version
    cursor.execute("SELECT version();")
    
    # Fetch result
    record = cursor.fetchone()
    
    print("\n✅ SUCCESS! Connected to:")
    print(record[0])

    # Close the connection
    cursor.close()
    connection.close()

except Exception as error:
    print("\n❌ FAILED to connect.")
    print(f"Error: {error}")