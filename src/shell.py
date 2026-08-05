"""
shell.py -- mini-sql交互式命令行

一个简单的SQL shell, 可以建表、插数据、查询。
数据存在内存里, 退出就没了(后面可以接上KV存储)。

用法: python -m src.shell

230511535 杨光裕
"""

import sys
import os

# Allow running as python src/shell.py from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine import Engine


def print_table(rows, max_width=80):
    """把查询结果格式化成表格打印"""
    if not rows:
        print("(empty)")
        return

    if isinstance(rows, str):
        print(rows)
        return

    if not isinstance(rows, list):
        print(rows)
        return

    # 获取所有列
    cols = list(rows[0].keys())
    if not cols:
        print("(no columns)")
        return

    # 算列宽
    col_widths = []
    for col in cols:
        w = len(str(col))
        for r in rows:
            w = max(w, len(str(r.get(col, "NULL"))))
        w = min(w, max_width // len(cols))  # 别太宽
        col_widths.append(w)

    # 打印表头分隔线
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    print(sep)

    # 表头
    header = "|"
    for i, col in enumerate(cols):
        header += f" {str(col):<{col_widths[i]}} |"
    print(header)
    print(sep)

    # 数据行
    for row in rows:
        line = "|"
        for i, col in enumerate(cols):
            val = str(row.get(col, "NULL"))
            if len(val) > col_widths[i]:
                val = val[:col_widths[i] - 1] + "."
            line += f" {val:<{col_widths[i]}} |"
        print(line)

    print(sep)
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def main():
    db = Engine()

    print("mini-sql shell v0.2")
    print("命令: SQL语句 | .tables | .help | .quit")
    print()

    while True:
        try:
            line = input("sql> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        if not line:
            continue

        # 点命令
        if line.startswith("."):
            cmd = line[1:].lower()
            if cmd in ("q", "quit", "exit"):
                break
            elif cmd == "tables":
                tables = db.tables
                if tables:
                    for t in tables:
                        print(f"  {t}")
                else:
                    print("  (no tables)")
            elif cmd == "help":
                print("  SQL: SELECT/INSERT/CREATE/DELETE/UPDATE")
                print("  点命令: .tables .help .quit")
                print("  例子:")
                print("    CREATE TABLE t (id INT, name STRING);")
                print("    INSERT INTO t (id, name) VALUES (1, 'hello');")
                print("    SELECT * FROM t WHERE id > 0 ORDER BY name LIMIT 5;")
            else:
                print(f"  未知命令: .{cmd}")
            continue

        # SQL
        try:
            result = db.execute(line)
            print_table(result)
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    main()
