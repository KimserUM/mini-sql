"""Test the SQL shell by importing and running db directly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import Engine

db = Engine()

# Create
r = db.execute("CREATE TABLE users (id INT, name STRING, age INT)")
print(f"create: {r}")

# Insert
r = db.execute("INSERT INTO users (id, name, age) VALUES (1, 'tom', 20)")
print(f"insert: {r}")
r = db.execute("INSERT INTO users (id, name, age) VALUES (2, 'alice', 22)")
print(f"insert: {r}")
r = db.execute("INSERT INTO users (id, name, age) VALUES (3, 'bob', 19)")
print(f"insert: {r}")

# Select
rows = db.execute("SELECT * FROM users")
print(f"select all: {len(rows)} rows")
for r in rows:
    print(f"  {r}")

# Update
r = db.execute("UPDATE users SET age = 21 WHERE id = 1")
print(f"update: {r}")
rows = db.execute("SELECT * FROM users WHERE id = 1")
assert rows[0]["age"] == 21
print(f"  verified: age={rows[0]['age']}")

# Projection
rows = db.execute("SELECT name, age FROM users WHERE age > 19 ORDER BY age DESC")
print(f"projection: {rows}")

# Tables
print(f"tables: {db.tables}")

print("shell test passed")
