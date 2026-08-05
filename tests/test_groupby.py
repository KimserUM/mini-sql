"""Test GROUP BY + aggregate functions + DROP TABLE."""
from src.engine import Engine

db = Engine()

# ── Setup ────────────────────────────────────
db.execute("CREATE TABLE emp (id INT, name STRING, dept STRING, salary INT)")
db.execute("INSERT INTO emp (id, name, dept, salary) VALUES (1, 'tom', 'eng', 80000)")
db.execute("INSERT INTO emp (id, name, dept, salary) VALUES (2, 'alice', 'eng', 90000)")
db.execute("INSERT INTO emp (id, name, dept, salary) VALUES (3, 'bob', 'sales', 70000)")
db.execute("INSERT INTO emp (id, name, dept, salary) VALUES (4, 'carol', 'sales', 75000)")
db.execute("INSERT INTO emp (id, name, dept, salary) VALUES (5, 'dave', 'hr', 65000)")

# ── Test 1: COUNT(*) per dept ────────────────
print("Test 1: COUNT(*) per dept")
rows = db.execute("SELECT dept, COUNT(*) FROM emp GROUP BY dept")
for r in rows:
    print(f"  {r}")
counts = {r['dept']: r['COUNT(*)'] for r in rows}
assert counts == {'eng': 2, 'sales': 2, 'hr': 1}, f"COUNT failed: {counts}"

# ── Test 2: AVG salary per dept ──────────────
print("Test 2: AVG(salary) per dept")
rows = db.execute("SELECT dept, AVG(salary) FROM emp GROUP BY dept")
for r in rows:
    print(f"  {r}")
avgs = {r['dept']: r['AVG(salary)'] for r in rows}
assert avgs['eng'] == 85000.0, f"AVG eng failed: {avgs['eng']}"
assert avgs['sales'] == 72500.0, f"AVG sales failed: {avgs['sales']}"
assert avgs['hr'] == 65000.0, f"AVG hr failed: {avgs['hr']}"

# ── Test 3: Global aggregates (no GROUP BY) ──
print("Test 3: Global aggregates")
rows = db.execute(
    "SELECT COUNT(*), SUM(salary), AVG(salary), MAX(salary), MIN(salary) FROM emp"
)
r = rows[0]
print(f"  {r}")
assert r['COUNT(*)'] == 5
assert r['SUM(salary)'] == 380000
assert r['AVG(salary)'] == 76000.0
assert r['MAX(salary)'] == 90000
assert r['MIN(salary)'] == 65000

# ── Test 4: GROUP BY + ORDER BY ──────────────
print("Test 4: GROUP BY + ORDER BY")
rows = db.execute(
    "SELECT dept, COUNT(*) FROM emp GROUP BY dept ORDER BY COUNT(*) DESC"
)
for r in rows:
    print(f"  {r}")
assert rows[0]['COUNT(*)'] >= rows[-1]['COUNT(*)'], "ORDER BY failed"

# ── Test 5: GROUP BY with WHERE ──────────────
print("Test 5: GROUP BY with WHERE filter")
rows = db.execute(
    "SELECT dept, COUNT(*) FROM emp WHERE salary > 70000 GROUP BY dept"
)
for r in rows:
    print(f"  {r}")
# eng: 2 (both > 70k), sales: 1 (only carol > 70k), hr: 0 (dave 65k)
counts2 = {r['dept']: r['COUNT(*)'] for r in rows}
assert counts2.get('eng') == 2, f"WHERE+GROUP eng failed: {counts2}"
assert counts2.get('sales') == 1, f"WHERE+GROUP sales failed: {counts2}"

# ── Test 6: GROUP BY + LIMIT ─────────────────
print("Test 6: GROUP BY + LIMIT")
rows = db.execute(
    "SELECT dept, COUNT(*) FROM emp GROUP BY dept ORDER BY dept LIMIT 2"
)
assert len(rows) == 2, f"LIMIT failed: {len(rows)}"

# ── Test 7: DROP TABLE ────────────────────────
print("Test 7: DROP TABLE")
db.execute("CREATE TABLE tmp (x INT)")
assert "tmp" in db.tables
result = db.execute("DROP TABLE tmp")
print(f"  {result}")
assert "tmp" not in db.tables

# ── Test 8: COUNT(column) excludes NULL ──────
print("Test 8: COUNT(column) excludes NULL")
db.execute("CREATE TABLE t (id INT, val INT)")
db.execute("INSERT INTO t (id, val) VALUES (1, 10)")
db.execute("INSERT INTO t (id, val) VALUES (2, NULL)")
rows = db.execute("SELECT COUNT(val), COUNT(*) FROM t")
print(f"  {rows[0]}")
assert rows[0]['COUNT(val)'] == 1, f"COUNT(col) should exclude NULL"
assert rows[0]['COUNT(*)'] == 2

print("\nAll GROUP BY / aggregation / DROP TABLE tests passed!")
