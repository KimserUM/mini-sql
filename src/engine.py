"""
engine.py — SQL执行引擎

在内存中维护表数据，执行解析出来的AST。
用Python dict模拟表结构：
  database = {
      "users": {
          "columns": [
              ColumnDef("id", "INT"),
              ColumnDef("name", "STRING"),
          ],
          "rows": [
              {"id": 1, "name": "tom"},
              {"id": 2, "name": "alice"},
          ]
      }
  }

支持:
  - SELECT + WHERE + ORDER BY + LIMIT
  - INSERT
  - CREATE TABLE
  - DELETE + WHERE

230511535 杨光裕 | 北理工CS考研复试准备
"""

from typing import Dict, List, Any, Optional
from src.parser import (
    Statment, SelectStmt, InsertStmt, CreateTableStmt, DeleteStmt,
    Expression, BinaryOp, ColumnRef, Literal, ColumnDef,
)
from src.tokenizer import Tokenizer
from src.parser import Parser


class EngineError(Exception):
    """执行错误"""
    pass


class Engine:
    """
    SQL执行引擎

    用法:
        db = Engine()
        db.execute("CREATE TABLE t (id INT, name STRING)")
        db.execute("INSERT INTO t (id, name) VALUES (1, 'hello')")
        result = db.execute("SELECT * FROM t")
        print(result)
    """

    def __init__(self):
        self._tables: Dict[str, Dict] = {}  # 所有表

    def execute(self, sql: str) -> Any:
        """执行一条SQL，返回结果"""
        # 词法 + 语法
        tokenizer = Tokenizer(sql)
        tokens = tokenizer.tokenize()
        parser = Parser(tokens)
        stmt = parser.parse()

        # 执行
        if isinstance(stmt, SelectStmt):
            return self._exec_select(stmt)
        elif isinstance(stmt, InsertStmt):
            return self._exec_insert(stmt)
        elif isinstance(stmt, CreateTableStmt):
            return self._exec_create_table(stmt)
        elif isinstance(stmt, DeleteStmt):
            return self._exec_delete(stmt)
        else:
            raise EngineError(f"不支持的语句类型: {type(stmt)}")

    # ── CREATE TABLE ────────────────────────

    def _exec_create_table(self, stmt: CreateTableStmt) -> str:
        if stmt.table in self._tables:
            raise EngineError(f"表 '{stmt.table}' 已存在")

        self._tables[stmt.table] = {
            "columns": stmt.columns,
            "rows": [],
        }
        return f"CREATE TABLE {stmt.table} ({len(stmt.columns)}列)"

    # ── INSERT ──────────────────────────────

    def _exec_insert(self, stmt: InsertStmt) -> str:
        table = self._get_table(stmt.table)

        if len(stmt.columns) != len(stmt.values):
            raise EngineError(
                f"列数({len(stmt.columns)})和值数({len(stmt.values)})不匹配"
            )

        # 类型转换
        row = {}
        for col_name, val in zip(stmt.columns, stmt.values):
            col_def = self._find_column(table, col_name)
            if col_def is None:
                raise EngineError(
                    f"表 '{stmt.table}' 没有列 '{col_name}'"
                )
            row[col_name] = self._convert_value(val, col_def.col_type)

        table["rows"].append(row)
        return f"INSERT 1 行"

    # ── SELECT ───────────────────────────────

    def _exec_select(self, stmt: SelectStmt) -> List[Dict]:
        table = self._get_table(stmt.table)

        # 1. WHERE过滤
        rows = table["rows"]
        if stmt.where:
            rows = [r for r in rows
                    if self._eval_expr(stmt.where, r)]

        # 2. ORDER BY排序
        if stmt.order_by:
            col_name = stmt.order_by
            desc = (stmt.order_dir.upper() == "DESC")
            rows = sorted(rows,
                          key=lambda r: self._sort_key(r.get(col_name)),
                          reverse=desc)

        # 3. LIMIT
        if stmt.limit is not None:
            rows = rows[:stmt.limit]

        # 4. 投影（选列）
        if stmt.columns == ['*']:
            return rows

        result = []
        for row in rows:
            projected = {}
            for col in stmt.columns:
                if col in row:
                    projected[col] = row[col]
            result.append(projected)

        return result

    # ── DELETE ───────────────────────────────

    def _exec_delete(self, stmt: DeleteStmt) -> str:
        table = self._get_table(stmt.table)

        if stmt.where is None:
            # DELETE所有行
            count = len(table["rows"])
            table["rows"] = []
            return f"DELETE {count} 行"

        before = len(table["rows"])
        table["rows"] = [
            r for r in table["rows"]
            if not self._eval_expr(stmt.where, r)
        ]
        deleted = before - len(table["rows"])
        return f"DELETE {deleted} 行"

    # ── 表达式求值 ──────────────────────────

    def _eval_expr(self, expr: Expression, row: Dict) -> Any:
        """在给定行上求值表达式，返回True/False（WHERE条件）"""
        if isinstance(expr, Literal):
            # 字面量不应该单独出现在WHERE中
            return expr.value

        if isinstance(expr, ColumnRef):
            return row.get(expr.name)

        if isinstance(expr, BinaryOp):
            left_val = self._eval_expr(expr.left, row)
            right_val = self._eval_expr(expr.right, row)
            op = expr.op

            # 比较运算
            if op == '=':
                return left_val == right_val
            elif op == '<>':
                return left_val != right_val
            elif op == '>':
                return self._cmp(left_val, right_val) > 0
            elif op == '<':
                return self._cmp(left_val, right_val) < 0
            elif op == '>=':
                return self._cmp(left_val, right_val) >= 0
            elif op == '<=':
                return self._cmp(left_val, right_val) <= 0
            elif op == 'AND':
                return bool(left_val) and bool(right_val)
            elif op == 'OR':
                return bool(left_val) or bool(right_val)
            else:
                raise EngineError(f"未知运算符: {op}")

        return False

    def _cmp(self, a: Any, b: Any) -> int:
        """比较两个值"""
        if a is None and b is None:
            return 0
        if a is None:
            return -1
        if b is None:
            return 1

        # 转成同类型比较
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a < b: return -1
            if a > b: return 1
            return 0
        return -1 if str(a) < str(b) else (1 if str(a) > str(b) else 0)

    def _sort_key(self, val: Any) -> Any:
        """排序用的key，NULL排最后"""
        if val is None:
            return (1, "")
        return (0, val)

    # ── 辅助 ────────────────────────────────

    def _get_table(self, name: str) -> Dict:
        if name not in self._tables:
            raise EngineError(f"表 '{name}' 不存在")
        return self._tables[name]

    def _find_column(self, table: Dict, name: str) -> Optional[ColumnDef]:
        for col in table["columns"]:
            if col.name == name:
                return col
        return None

    def _convert_value(self, val: str, col_type: str) -> Any:
        """类型转换"""
        if val.upper() == "NULL":
            return None
        if col_type == "INT":
            try:
                return int(val)
            except ValueError:
                raise EngineError(f"无法将 '{val}' 转为 INT")
        elif col_type == "FLOAT":
            try:
                return float(val)
            except ValueError:
                raise EngineError(f"无法将 '{val}' 转为 FLOAT")
        return val  # STRING

    @property
    def tables(self) -> List[str]:
        return list(self._tables.keys())


# ── 测试 ──
if __name__ == "__main__":
    db = Engine()

    # 建表
    print(db.execute("CREATE TABLE users (id INT, name STRING, age INT)"))
    print(db.execute(
        "CREATE TABLE scores (student STRING, course STRING, score INT)"
    ))

    # 插入
    print(db.execute(
        "INSERT INTO users (id, name, age) VALUES (1, 'tom', 20)"
    ))
    print(db.execute(
        "INSERT INTO users (id, name, age) VALUES (2, 'alice', 22)"
    ))
    print(db.execute(
        "INSERT INTO users (id, name, age) VALUES (3, 'bob', 19)"
    ))
    print(db.execute(
        "INSERT INTO users (id, name, age) VALUES (4, 'carol', 25)"
    ))

    # 查询
    print("\n--- 全表查询 ---")
    rows = db.execute("SELECT * FROM users")
    for r in rows:
        print(f"  {r}")

    print("\n--- WHERE过滤 ---")
    rows = db.execute("SELECT * FROM users WHERE age >= 20")
    for r in rows:
        print(f"  {r}")

    print("\n--- 投影 ---")
    rows = db.execute("SELECT name, age FROM users WHERE age > 20")
    for r in rows:
        print(f"  {r}")

    print("\n--- ORDER BY ---")
    rows = db.execute("SELECT * FROM users ORDER BY age DESC")
    for r in rows:
        print(f"  {r}")

    print("\n--- LIMIT ---")
    rows = db.execute("SELECT * FROM users LIMIT 2")
    for r in rows:
        print(f"  {r}")

    print("\n--- AND条件 ---")
    rows = db.execute(
        "SELECT * FROM users WHERE age >= 20 AND age <= 25"
    )
    for r in rows:
        print(f"  {r}")

    # 删除
    print(f"\n{db.execute('DELETE FROM users WHERE age < 20')}")
    rows = db.execute("SELECT * FROM users")
    print(f"剩余 {len(rows)} 行")
    for r in rows:
        print(f"  {r}")

    print("\n引擎测试完成!")
