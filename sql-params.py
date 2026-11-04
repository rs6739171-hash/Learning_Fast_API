from dns.tsig import Key
from rich.repr import Result
from typing import Any
import sqlite3
from schemas_fields import Product, ProductCreate, ProductUpdate


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('products.db', check_same_thread=False)
        self.cur = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cur.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
)
''')

    def create(self,product:ProductCreate):
        # find the next id
        self.cur.execute('SELECT MAX(id) FROM products')
        result = self.cur.fetchone()

        new_id = (result[0] or 0) + 1

        self.cur.execute('''
            INSERT  INTO products (id,name,price,stock,status)
            VALUES (:id,:name,:price,:stock'''
            ,{
                id:new_id,
                **product.model_dump()
            })
        self.conn.commit()
        return new_id

    def get(self,id: int)-> dict[str,Any] | None:
        self.cur.execute('''SELECT * FROM products WHERE id =
        :id''',{'id':id})
        result = self.cur.fetchone()
        
        return {
                'id':result[0],
                'name':result[1],
                 'price':result[2],
                 'stock':result[3]
            } if result else None

    def update(self,id:int,Product_update:ProductUpdate):
        
        data = Product_update.model_dump(exclude_none=True)
        set_clause = ','.join(f"{key}=:{key}" for key in data)
        
        self.cur.execute('''
        UPDATE products
        SET '''+ set_clause +'''
        WHERE id = :id'''
        ,{
            'id':id,
            **data
        })
        self.conn.commit()
        return self.get(id)

    def delete(self,id:int):
        self.cur.execute('DELETE FROM products WHERE id = :id',{'id':id})
        self.conn.commit()

    def close(self):
        self.conn.close()