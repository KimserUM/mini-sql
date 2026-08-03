"""
tokenizer.py — SQL词法分析器

把SQL字符串拆成token序列，给parser用。
手写的状态机，没用regex（学编译原理时写的）

Token类型:
  - KEYWORD: SELECT, FROM, WHERE, INSERT, CREATE, TABLE, INTO, VALUES, AND, OR
  - IDENTIFIER: 表名、列名
  - NUMBER: 整数、浮点数
  - STRING: 'hello world'
  - OPERATOR: =, >, <, >=, <=, <>, (, ), *, ,
  - EOF: 结束

230511535 杨光裕 | 北理工CS考研复试准备
"""

from enum import Enum, auto
from typing import List, Tuple


class TokenType(Enum):
    # 关键字
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    CREATE = auto()
    TABLE = auto()
    AND = auto()
    OR = auto()
    ORDER = auto()
    BY = auto()
    ASC = auto()
    DESC = auto()
    LIMIT = auto()
    DELETE = auto()
    UPDATE = auto()
    SET = auto()
    DROP = auto()
    NOT = auto()
    NULL = auto()

    # 标识符和字面量
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # 运算符
    STAR = auto()      # *
    COMMA = auto()     # ,
    LPAREN = auto()    # (
    RPAREN = auto()    # )
    EQUALS = auto()    # =
    GT = auto()        # >
    LT = auto()        # <
    GE = auto()        # >=
    LE = auto()        # <=
    NE = auto()        # <>

    # 其他
    SEMICOLON = auto() # ;
    EOF = auto()


# 关键字映射
KEYWORDS = {
    "SELECT": TokenType.SELECT,
    "FROM": TokenType.FROM,
    "WHERE": TokenType.WHERE,
    "INSERT": TokenType.INSERT,
    "INTO": TokenType.INTO,
    "VALUES": TokenType.VALUES,
    "CREATE": TokenType.CREATE,
    "TABLE": TokenType.TABLE,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "ORDER": TokenType.ORDER,
    "BY": TokenType.BY,
    "ASC": TokenType.ASC,
    "DESC": TokenType.DESC,
    "LIMIT": TokenType.LIMIT,
    "DELETE": TokenType.DELETE,
    "UPDATE": TokenType.UPDATE,
    "SET": TokenType.SET,
    "DROP": TokenType.DROP,
    "NOT": TokenType.NOT,
    "NULL": TokenType.NULL,
}


class Token:
    """一个词法单元"""
    def __init__(self, token_type: TokenType, value: str,
                 line: int = 0, col: int = 0):
        self.type = token_type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"<{self.type.name} '{self.value}'>"


class TokenizerError(Exception):
    """词法错误"""
    def __init__(self, msg, line, col):
        super().__init__(f"[行{line} 列{col}] {msg}")
        self.line = line
        self.col = col


class Tokenizer:
    """
    SQL词法分析器

    用法:
        t = Tokenizer("SELECT * FROM users WHERE id = 1")
        tokens = t.tokenize()
    """

    def __init__(self, sql: str):
        self.sql = sql
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self) -> str:
        """看当前字符"""
        if self.pos < len(self.sql):
            return self.sql[self.pos]
        return '\0'

    def _advance(self) -> str:
        """前进一个字符"""
        ch = self.sql[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace(self):
        """跳过空白"""
        while self._peek() in ' \t\n\r':
            self._advance()

    def _skip_comment(self):
        """跳过 -- 注释"""
        # 单行注释
        if self._peek() == '-' and self.pos + 1 < len(self.sql) \
                and self.sql[self.pos + 1] == '-':
            while self._peek() != '\n' and self._peek() != '\0':
                self._advance()

    def _read_word(self) -> str:
        """读一个单词（字母/数字/下划线）"""
        start = self.pos
        while self._peek().isalnum() or self._peek() == '_':
            self._advance()
        return self.sql[start:self.pos]

    def _read_number(self) -> Token:
        """读一个数字"""
        start = self.pos
        while self._peek().isdigit():
            self._advance()
        if self._peek() == '.':
            self._advance()
            while self._peek().isdigit():
                self._advance()
        return Token(TokenType.NUMBER, self.sql[start:self.pos],
                     self.line, self.col)

    def _read_string(self) -> Token:
        """读一个字符串 '...' """
        self._advance()  # 跳过开头的 '
        start = self.pos
        while self._peek() != '\'' and self._peek() != '\0':
            if self._peek() == '\\':
                self._advance()  # 跳过转义
            self._advance()
        val = self.sql[start:self.pos]
        if self._peek() == '\'':
            self._advance()  # 跳过结尾的 '
        return Token(TokenType.STRING, val, self.line, self.col)

    def tokenize(self) -> List[Token]:
        """主入口：分词"""
        tokens = []

        while self.pos < len(self.sql):
            self._skip_whitespace()
            self._skip_comment()
            self._skip_whitespace()

            if self.pos >= len(self.sql):
                break

            ch = self._peek()
            line, col = self.line, self.col

            # 数字
            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            # 字符串
            if ch == '\'':
                tokens.append(self._read_string())
                continue

            # 单词（可能是关键字或标识符）
            if ch.isalpha() or ch == '_':
                word = self._read_word()
                upper = word.upper()
                if upper in KEYWORDS:
                    tokens.append(Token(KEYWORDS[upper], word,
                                        line, col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, word,
                                        line, col))
                continue

            # 符号
            self._advance()
            if ch == '*':
                tokens.append(Token(TokenType.STAR, '*', line, col))
            elif ch == ',':
                tokens.append(Token(TokenType.COMMA, ',', line, col))
            elif ch == '(':
                tokens.append(Token(TokenType.LPAREN, '(', line, col))
            elif ch == ')':
                tokens.append(Token(TokenType.RPAREN, ')', line, col))
            elif ch == '=':
                tokens.append(Token(TokenType.EQUALS, '=', line, col))
            elif ch == '>':
                if self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.GE, '>=', line, col))
                else:
                    tokens.append(Token(TokenType.GT, '>', line, col))
            elif ch == '<':
                if self._peek() == '>':
                    self._advance()
                    tokens.append(Token(TokenType.NE, '<>', line, col))
                elif self._peek() == '=':
                    self._advance()
                    tokens.append(Token(TokenType.LE, '<=', line, col))
                else:
                    tokens.append(Token(TokenType.LT, '<', line, col))
            elif ch == ';':
                tokens.append(Token(TokenType.SEMICOLON, ';', line, col))
            else:
                raise TokenizerError(
                    f"不认识的字符: '{ch}'",
                    line, col
                )

        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens


# ── 测试 ──
if __name__ == "__main__":
    tests = [
        "SELECT * FROM users WHERE id = 1",
        "INSERT INTO users (name, age) VALUES ('tom', 25)",
        "CREATE TABLE users (id INT, name STRING)",
        "SELECT name, age FROM users WHERE age >= 18 AND name <> 'admin'",
        "DELETE FROM users WHERE id = 5",
        "SELECT * FROM t ORDER BY id DESC LIMIT 10",
    ]

    for sql in tests:
        print(f"\nSQL: {sql}")
        try:
            t = Tokenizer(sql)
            tokens = t.tokenize()
            for tok in tokens:
                print(f"  {tok}")
        except TokenizerError as e:
            print(f"  词法错误: {e}")

    print("\n词法分析器测试完成")
