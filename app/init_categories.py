#!/usr/bin/env python
"""
Script to initialize default categories in the database.
Run this once to ensure all default categories are present.
"""

import mysql.connector
from app.config import HOST, USER, PASSWORD, DATABASE

def init_categories():
    """Initialize default categories in the database"""
    default_categories = [
        'Hardware',
        'Software',
        'Conexão com Internet',
        'Acessos',
        'Sistemas',
        'Segurança',
        'Impressora',
        'Telefone/Celular',
        'Outros'
    ]

    try:
        # Parse HOST to extract host and port
        host_parts = HOST.split(':')
        db_host = host_parts[0]
        db_port = int(host_parts[1]) if len(host_parts) > 1 else 3306

        db_config = {
            'host': db_host,
            'port': db_port,
            'user': USER,
            'password': PASSWORD,
            'database': DATABASE
        }

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        print("Initializing default categories...")
        
        for category in default_categories:
            # Check if category already exists
            cursor.execute("SELECT id FROM categorias WHERE nome = %s", (category,))
            result = cursor.fetchone()
            
            if not result:
                cursor.execute("INSERT INTO categorias (nome) VALUES (%s)", (category,))
                conn.commit()
                print(f"  ✓ Inserted: {category}")
            else:
                print(f"  ✓ Already exists: {category} (ID: {result['id']})")
        
        print("\n✓ Categories initialized successfully!")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"✗ Error initializing categories: {str(e)}")
        raise

if __name__ == "__main__":
    init_categories()
