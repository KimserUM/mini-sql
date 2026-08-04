"""
parser.py — SQL语法分析器（递归下降）

把token序列解析成AST(抽象语法树)。
递归下降写起来比较直观——每个语法规则一个函数。

支持语法：
  SELECT [cols] FROM table [WHERE cond] [ORDER BY col [ASC|DESC]] [LIMIT n]
  INSERT INTO table (cols) VALUES (vals)
  CREATE TABLE name (col type, col type, ...)
  DELETE FROM table [WHERE cond]

AST用Python dataclass表示，结构清晰一点。

参考了《数据库系统概念》和sqlite的语法文档

230511535 杨光裕 | 北理工CS考研复试准备
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from src.tokenizer import Tokenizer, Token, TokenType


# ── AST节点 ──────────────────────────────

@dataclass
class ColumnDef:
    """列定义"""
    name: str
    col_type: str  # INT / STRING / FLOAT

@dataclass
class Expression:
    """表达式（WHERE条件）"""
    pass

@dataclass
class BinaryOp(Expression):
    """二元运算: a = b, a > b, a AND b ..."""
    op: str          # =, >, <, >=, <=, <>, AND, OR
    left: Expression
    right: Expression

@dataclass
class ColumnRef(Expression):
    """列引用"""
    name: str

@dataclass
class Literal(Expression):
    """字面量"""
    value: str
    lit_type: str    # number / string / null

@dataclass
class SelectStmt:
    """SELECT语句"""
    columns: List[str]         # 选哪几列, ['*'] 表示全部
    table: str
    where: Optional[Expression] = None
    order_by: Optional[str] = None
    order_dir: str = "ASC"
    limit: Optional[int] = None

@dataclass
class InsertStmt:
    """INSERT语句"""
    table: str
    columns: List[str]
    values: List[str]

@dataclass
class CreateTableStmt:
    """CREATE TABLE语句"""
    table: str
    columns: List[ColumnDef]

@dataclass
class DeleteStmt:
    """DELETE语句"""
    table: str
    where: Optional[Expression] = None

@dataclass
class UpdateStmt:
    """UPDATE语句"""
    table: str
    assignments: Dict[str, str]   # col -> new_value
    where: Optional[Expression] = None

Statment = SelectStmt | InsertStmt | CreateTableStmt | DeleteStmt | UpdateStmt


# ── Parser ─────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg, token=None):
        if token:
            super().__init__(
                f"[行{token.line} 列{token.col}] {msg}, "
                f"got '{token.value}'"
            )
        else:
            super().__init__(msg)


class Parser:
    """
    SQL递归下降解析器

    用法:
        t = Tokenizer("SELECT * FROM t")
        p = Parser(t.tokenize())
        stmt = p.parse()
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, token_type: TokenType) -> Token:
        """期望下一个token是某类型，否则报错"""
        tok = self._advance()
        if tok.type != token_type:
            raise ParseError(
                f"期望 {token_type.name}", tok
            )
        return tok

    def _match(self, token_type: TokenType) -> bool:
        """如果当前token类型匹配，吃掉并返回True"""
        if self._peek().type == token_type:
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        """只检查不消费"""
        return self._peek().type == token_type

    # ── 顶层入口 ──────────────────────────

    def parse(self) -> Statment:
        """解析入口"""
        tok = self._peek()

        if tok.type == TokenType.SELECT:
            return self._parse_select()
        elif tok.type == TokenType.INSERT:
            return self._parse_insert()
        elif tok.type == TokenType.CREATE:
            return self._parse_create_table()
        elif tok.type == TokenType.DELETE:
            return self._parse_delete()
        elif tok.type == TokenType.UPDATE:
            return self._parse_update()
        else:
            raise ParseError(f"不支持的语句, 以{tok.type.name}开头", tok)

    # ── SELECT ────────────────────────────

    def _parse_select(self) -> SelectStmt:
        """SELECT [cols] FROM table [WHERE cond] [ORDER BY...] [LIMIT n]"""
        self._expect(TokenType.SELECT)

        # 列列表
        columns = self._parse_column_list()

        # FROM
        self._expect(TokenType.FROM)
        table_token = self._expect(TokenType.IDENTIFIER)
        table = table_token.value

        # WHERE (可选)
        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_expression()

        # ORDER BY (可选)
        order_by = None
        order_dir = "ASC"
        if self._match(TokenType.ORDER):
            self._expect(TokenType.BY)
            order_token = self._expect(TokenType.IDENTIFIER)
            order_by = order_token.value
            if self._check(TokenType.ASC) or self._check(TokenType.DESC):
                order_dir = self._advance().value

        # LIMIT (可选)
        limit = None
        if self._match(TokenType.LIMIT):
            limit_token = self._expect(TokenType.NUMBER)
            limit = int(limit_token.value)

        # 可选的;
        self._match(TokenType.SEMICOLON)

        return SelectStmt(
            columns=columns,
            table=table,
            where=where,
            order_by=order_by,
            order_dir=order_dir,
            limit=limit,
        )

    def _parse_column_list(self) -> List[str]:
        """列名列表: * | col1, col2, ..."""
        if self._match(TokenType.STAR):
            return ['*']

        cols = []
        tok = self._expect(TokenType.IDENTIFIER)
        cols.append(tok.value)

        while self._match(TokenType.COMMA):
            tok = self._expect(TokenType.IDENTIFIER)
            cols.append(tok.value)

        return cols

    # ── INSERT ─────────────────────────────

    def _parse_insert(self) -> InsertStmt:
        """INSERT INTO table (cols) VALUES (vals)"""
        self._expect(TokenType.INSERT)
        self._expect(TokenType.INTO)
        table = self._expect(TokenType.IDENTIFIER).value

        # 列名
        self._expect(TokenType.LPAREN)
        columns = []
        col = self._expect(TokenType.IDENTIFIER)
        columns.append(col.value)
        while self._match(TokenType.COMMA):
            col = self._expect(TokenType.IDENTIFIER)
            columns.append(col.value)
        self._expect(TokenType.RPAREN)

        # VALUES
        self._expect(TokenType.VALUES)
        self._expect(TokenType.LPAREN)
        values = []
        val = self._parse_value()
        values.append(val)
        while self._match(TokenType.COMMA):
            values.append(self._parse_value())
        self._expect(TokenType.RPAREN)

        self._match(TokenType.SEMICOLON)

        return InsertStmt(table=table, columns=columns, values=values)

    def _parse_value(self) -> str:
        """一个字面量"""
        tok = self._peek()
        if tok.type == TokenType.NUMBER:
            return self._advance().value
        elif tok.type == TokenType.STRING:
            return self._advance().value
        elif tok.type == TokenType.IDENTIFIER:
            val = self._advance().value
            if val.upper() == "NULL":
                return "NULL"
            return val
        else:
            raise ParseError("期望数字或字符串", tok)

    # ── CREATE TABLE ────────────────────────

    def _parse_create_table(self) -> CreateTableStmt:
        """CREATE TABLE name (col1 type1, col2 type2, ...)"""
        self._expect(TokenType.CREATE)
        self._expect(TokenType.TABLE)
        table = self._expect(TokenType.IDENTIFIER).value

        self._expect(TokenType.LPAREN)
        columns = []

        # 第一个列
        col = self._parse_column_def()
        columns.append(col)

        while self._match(TokenType.COMMA):
            col = self._parse_column_def()
            columns.append(col)

        self._expect(TokenType.RPAREN)
        self._match(TokenType.SEMICOLON)

        return CreateTableStmt(table=table, columns=columns)

    def _parse_column_def(self) -> ColumnDef:
        """col_name col_type"""
        name = self._expect(TokenType.IDENTIFIER).value
        type_tok = self._expect(TokenType.IDENTIFIER)
        col_type = type_tok.value.upper()
        if col_type not in ("INT", "STRING", "FLOAT"):
            raise ParseError(
                f"不支持的类型: {col_type}, 应该是 INT/STRING/FLOAT",
                type_tok
            )
        return ColumnDef(name=name, col_type=col_type)

    # ── DELETE ──────────────────────────────

    def _parse_delete(self) -> DeleteStmt:
        """DELETE FROM table [WHERE cond]"""
        self._expect(TokenType.DELETE)
        self._expect(TokenType.FROM)
        table = self._expect(TokenType.IDENTIFIER).value

        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_expression()

        self._match(TokenType.SEMICOLON)

        return DeleteStmt(table=table, where=where)

    def _parse_update(self) -> UpdateStmt:
        """UPDATE table SET col=val, col=val... [WHERE cond]"""
        self._expect(TokenType.UPDATE)
        table = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.SET)

        # col = value pairs
        assignments: Dict[str, str] = {}
        col = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.EQUALS)
        assignments[col] = self._parse_value()

        while self._match(TokenType.COMMA):
            col = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.EQUALS)
            assignments[col] = self._parse_value()

        where = None
        if self._match(TokenType.WHERE):
            where = self._parse_expression()

        self._match(TokenType.SEMICOLON)

        return UpdateStmt(table=table, assignments=assignments, where=where)

    # ── 表达式解析 ──────────────────────────

    def _parse_expression(self) -> Expression:
        """
        递归下降解析WHERE表达式
        优先级: OR < AND < 比较 < 基本单元

        expr    = and_expr (OR and_expr)*
        and_expr = comp_expr (AND comp_expr)*
        comp_expr = atom (比较符 atom)?
        atom     = 列名 | 字面量 | ( expr )
        """
        return self._parse_or()

    def _parse_or(self) -> Expression:
        left = self._parse_and()
        while self._match(TokenType.OR):
            right = self._parse_and()
            left = BinaryOp(op="OR", left=left, right=right)
        return left

    def _parse_and(self) -> Expression:
        left = self._parse_comparison()
        while self._match(TokenType.AND):
            right = self._parse_comparison()
            left = BinaryOp(op="AND", left=left, right=right)
        return left

    def _parse_comparison(self) -> Expression:
        left = self._parse_atom()
        tok = self._peek()

        # 比较运算符
        if tok.type in (TokenType.EQUALS, TokenType.GT, TokenType.LT,
                        TokenType.GE, TokenType.LE, TokenType.NE):
            self._advance()
            right = self._parse_atom()
            return BinaryOp(op=tok.value, left=left, right=right)

        return left

    def _parse_atom(self) -> Expression:
        """基本单元：列名、字面量、括号"""
        tok = self._peek()

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            if tok.value.upper() == "NULL":
                return Literal(value="NULL", lit_type="null")
            return ColumnRef(name=tok.value)

        if tok.type == TokenType.NUMBER:
            self._advance()
            return Literal(value=tok.value, lit_type="number")

        if tok.type == TokenType.STRING:
            self._advance()
            return Literal(value=tok.value, lit_type="string")

        raise ParseError(f"表达式语法错误", tok)


# ── 测试 ──
if __name__ == "__main__":
    tests = [
        "SELECT * FROM users",
        "SELECT name, age FROM users WHERE age >= 18",
        "SELECT * FROM users WHERE name = 'tom' AND age > 20",
        "INSERT INTO users (name, age) VALUES ('alice', 25)",
        "CREATE TABLE users (id INT, name STRING, score FLOAT)",
        "DELETE FROM users WHERE id = 5",
        "SELECT * FROM t ORDER BY id DESC LIMIT 10",
    ]

    for sql in tests:
        print(f"\nSQL: {sql}")
        try:
            t = Tokenizer(sql)
            p = Parser(t.tokenize())
            stmt = p.parse()
            print(f"  => {stmt}")
        except (Exception, ParseError) as e:
            print(f"  解析错误: {e}")

    print("\n语法分析器测试完成")
