import sqlite3

conn = sqlite3.connect("product.db")

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    status TEXT NOT NULL
    )
''')

# insert row in table od database
#cursor.execute('''
#INSERT  INTO products (id,name,price,stock,status)
#VALUES (1002,'Wireless Mouse Pro',18.99,42,'active')
#''')

# Select all rows from DB
cursor.execute('Select * from products')

# Fethch all results
all_rows = cursor.fetchall()
print (all_rows)

# commit the changes and close thne connection

conn.commit()
# Close when done
conn.close()