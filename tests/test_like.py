"""Test LIKE pattern matching in WHERE clauses."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.engine import Engine

db = Engine()

# Setup
db.execute("CREATE TABLE users (id INT, name STRING, email STRING)")
db.execute("INSERT INTO users (id, name, email) VALUES (1, 'tom', 'tom@example.com')")
db.execute("INSERT INTO users (id, name, email) VALUES (2, 'alice', 'alice@test.org')")
db.execute("INSERT INTO users (id, name, email) VALUES (3, 'tommy', 'tommy@example.com')")
db.execute("INSERT INTO users (id, name, email) VALUES (4, 'bob', 'bob@test.com')")

# Test 1: Basic LIKE with % wildcard (prefix match)
print("Test 1: name LIKE 'tom%'")
rows = db.execute("SELECT * FROM users WHERE name LIKE 'tom%'")
names = [r['name'] for r in rows]
print(f"  -> {names}")
assert names == ['tom', 'tommy'], f"Expected ['tom', 'tommy'], got {names}"

# Test 2: LIKE with % at end (suffix match)
print("Test 2: email LIKE '%@example.com'")
rows = db.execute("SELECT * FROM users WHERE email LIKE '%@example.com'")
emails = [r['email'] for r in rows]
print(f"  -> {emails}")
assert len(rows) == 2, f"Expected 2, got {len(rows)}"
assert all('@example.com' in e for e in emails)

# Test 3: LIKE with _ single-char wildcard
print("Test 3: name LIKE 't_m'")
rows = db.execute("SELECT * FROM users WHERE name LIKE 't_m'")
names = [r['name'] for r in rows]
print(f"  -> {names}")
assert names == ['tom'], f"Expected ['tom'], got {names}"

# Test 4: LIKE with both % and _
print("Test 4: name LIKE '_o%'")
rows = db.execute("SELECT * FROM users WHERE name LIKE '_o%'")
names = [r['name'] for r in rows]
print(f"  -> {names}")
# tom, tommy both start with 'to', bob starts with 'bo'
assert 'tom' in names
assert 'tommy' in names
assert 'bob' in names
assert 'alice' not in names

# Test 5: LIKE with no wildcard (exact match)
print("Test 5: name LIKE 'bob'")
rows = db.execute("SELECT * FROM users WHERE name LIKE 'bob'")
print(f"  -> {len(rows)} row(s)")
assert len(rows) == 1
assert rows[0]['name'] == 'bob'

# Test 6: LIKE combined with AND
print("Test 6: name LIKE '%m%' AND id > 1")
rows = db.execute("SELECT * FROM users WHERE name LIKE '%m%' AND id > 1")
names = [r['name'] for r in rows]
print(f"  -> {names}")
assert 'tommy' in names
assert 'tom' not in names  # id=1 excluded

# Test 7: LIKE with NULL column value
print("Test 7: LIKE on NULL value")
db.execute("CREATE TABLE t (id INT, name STRING)")
db.execute("INSERT INTO t (id, name) VALUES (1, NULL)")
db.execute("INSERT INTO t (id, name) VALUES (2, 'hello')")
rows = db.execute("SELECT * FROM t WHERE name LIKE '%'")
print(f"  -> {len(rows)} row(s)")
assert len(rows) == 1  # NULL doesn't match LIKE
assert rows[0]['name'] == 'hello'

print("\nAll LIKE tests passed!")
