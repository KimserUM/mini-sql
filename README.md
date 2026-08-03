# mini-sql

一个迷你的SQL解析器和执行引擎。考研复试项目 #4  
*（2026.08 从旧GitHub账号迁移过来）*

## 起因

数据库课上学了SQL怎么写，但从来不知道SQL底层是怎么实现的。
看了《数据库系统概念》和SQLite的源码，想自己实现一个简单的。

实际写下来发现编译器那套知识（词法分析、语法分析、AST）很有用，
正好编译原理也是复试常考的内容。

## 架构

```
SQL文本
  │
  ▼
┌─────────────┐
│  Tokenizer  │  词法分析: SQL字符串 → Token序列
│  (手写状态机) │     SELECT → [SELECT][*][FROM][users]...
└──────┬──────┘
       │ tokens
       ▼
┌─────────────┐
│   Parser    │  语法分析: Token序列 → AST
│  (递归下降)  │     递归下降，每个语法规则一个函数
└──────┬──────┘
       │ AST
       ▼
┌─────────────┐
│   Engine    │  执行引擎: AST → 结果
│  (内存表)   │     表数据用Python dict/simulate
└─────────────┘
```

## 支持的功能

```sql
-- DDL
CREATE TABLE users (id INT, name STRING, age INT);

-- DML
INSERT INTO users (id, name, age) VALUES (1, 'tom', 20);
INSERT INTO users (id, name, age) VALUES (2, 'alice', 22);

-- 查询
SELECT * FROM users;
SELECT name, age FROM users WHERE age >= 20;
SELECT * FROM users WHERE name = 'tom' AND age > 18;
SELECT * FROM users ORDER BY age DESC LIMIT 5;

-- 删除
DELETE FROM users WHERE id = 3;
DELETE FROM users;  -- 全删
```

## 不支持（故意的，太复杂了）

- JOIN（多表查询）
- 子查询
- GROUP BY / HAVING
- UPDATE
- 索引
- 事务

## 怎么跑

```python
from src.engine import Engine

db = Engine()
db.execute("CREATE TABLE t (id INT, name STRING)")
db.execute("INSERT INTO t (id, name) VALUES (1, 'hello')")
result = db.execute("SELECT * FROM t")
print(result)
```

或者直接跑测试:

```bash
python -m src.engine
```

## 实现细节

### 词法分析

手写的状态机。看了网上很多教程说用flex/regex，但我觉得手写更能理解原理。

状态机的几个关键状态:
- 空白: 跳过
- 数字: 一直读到非数字
- 字母: 一直读到非字母数字，然后查关键字表
- 单引号: 字符串，读到下一个单引号
- 符号: 单字符(, * =) 或双字符(>= <= <>)

### 语法分析

递归下降。每个语法规则对应一个解析函数:

```
parse()        → parse_select / parse_insert / parse_create / parse_delete
parse_select() → SELECT cols FROM table [WHERE expr] [ORDER BY ...]
parse_expr()   → parse_or → parse_and → parse_cmp → parse_atom
```

优先级通过函数调用层次保证（OR < AND < 比较 < 原子）。

### 执行引擎

表数据就存在 Python dict 里:
- 列定义: 一个 list of ColumnDef
- 行数据: list of dict (每行是一个dict)

WHERE条件通过递归遍历AST节点来求值:
- ColumnRef: 从当前行取值
- Literal: 返回字面量
- BinaryOp: 递归求左右子树，然后运算

### 类型转换

INSERT的时候做类型检查（INT → int, FLOAT → float）
NULL的处理: 排序时NULL排最后

## 踩坑

1. Tokenizer一开始用正则，结果遇到字符串里的逗号就炸了。改成了手写状态机
2. 递归下降的优先级: 一开始把AND/OR当同级处理，结果 `a > 1 OR b > 2 AND c > 3` 的语义不对
3. WHERE表达式求值时NULL的处理: NULL参与比较的结果不是true/false而是NULL (三值逻辑)，这里简化成NULL < 任何值
4. ORDER BY时不同数据类型不能直接比较，要统一转成(str,)元组

## 文件

```
mini-sql/
├── src/
│   ├── tokenizer.py   词法分析
│   ├── parser.py      语法分析
│   └── engine.py      执行引擎
└── tests/
```

---

230511535 杨光裕 | 2026.08 | 北理工CS考研复试准备
