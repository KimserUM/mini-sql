"""Test UPDATE statement."""
from src.engine import Engine

db = Engine()

# Setup
db.execute("CREATE TABLE users (id INT, name STRING, age INT)")
db.execute("INSERT INTO users (id, name, age) VALUES (1, 'tom', 20)")
db.execute("INSERT INTO users (id, name, age) VALUES (2, 'alice', 22)")
db.execute("INSERT INTO users (id, name, age) VALUES (3, 'bob', 19)")

# Test UPDATE single column
result = db.execute("UPDATE users SET age = 21 WHERE id = 1")
print(result)

# Test UPDATE multiple columns
result = db.execute("UPDATE users SET name = 'carol', age = 25 WHERE id = 3")
print(result)

# Verify
rows = db.execute("SELECT * FROM users")
for r in rows:
    print(f"  {r}")

# Expected: tom age=21, alice age=22, carol age=25
assert rows[0]["age"] == 21, f"expected 21, got {rows[0]['age']}"
assert rows[1]["age"] == 22
assert rows[2]["name"] == "carol"
assert rows[2]["age"] == 25

print("UPDATE test passed!")
