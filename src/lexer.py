# C语言词法分析器
# /src/lexer.py
import sys


class Token:
    """
    词法分析器的token类

    提供的方法：
    - `token_type() -> str`: 返回token的类型
    - `token_value() -> str`: 返回token的值
    - `line() -> int`: 返回token所在的行号
    - `column() -> int`: 返回token所在的列号
    - `tupleization() -> Tuple[str, str, int, int]`: 返回元组形式的token
    """

    def __init__(self, token_type, token_value, line, column):
        self._token_type = token_type
        self._token_value = token_value
        self._line = line
        self._column = column

    def __str__(self):
        return f"line {self._line}, column {self._column}: ({self._token_type})  {self._token_value}"

    def __eq__(self, other):
        return (
            self._token_type == other.token_type()
            and self._token_value == other.token_value()
            and self._line == other.line()
            and self._column == other.column()
        )

    def token_type(self):
        return self._token_type

    def token_value(self):
        return self._token_value

    def line(self):
        return self._line

    def column(self):
        return self._column

    def tupleization(self):
        # 返回元组形式的token
        return (self._token_type, self._token_value, self._line, self._column)


class Lexer:
    """
    C语言词法分析器

    提供的方法：
    - `tokenize(code: str) -> None`: 对输入的C语言代码进行词法分析
    - `tokenize_result() -> List[Token]`: 返回词法分析结果
    - `code() -> str`: 返回上次词法分析的代码
    """

    def __init__(self):
        # 初始化关键字和标点符号
        self._keywords = {
            "int": "int",
            "char": "char",
            "float": "float",
            "double": "double",
            "void": "void",
            "if": "if",
            "else": "else",
            "while": "while",
            "for": "for",
            "do": "do",
            "return": "return",
            "break": "break",
            "continue": "continue",
            "#include": "include",
            "#define": "define",
            "stdin": "stdin",
            "stdout": "stdout",
            "stderr": "stderr",
        }

        self._punctuators = {
            "++": "plusplus",
            "--": "minusminus",
            "+": "plus",
            "-": "minus",
            "*": "times",
            "/": "divide",
            "%": "percent",
            "==": "eq",
            "!=": "neq",
            ">=": "ge",
            "<=": "le",
            ">": "gt",
            "<": "lt",
            "&&": "logical_and",
            "||": "logical_or",
            "!": "logical_not",
            "&": "bitwise_and",
            "|": "bitwise_or",
            "^": "bitwise_xor",
            "~": "bitwise_not",
            "=": "assign",
            ",": "comma",
            ";": "semicolon",
            ":": "colon",
            ".": "dot",
            "(": "lparen",
            ")": "rparen",
            "[": "lbracket",
            "]": "rbracket",
            "{": "lbrace",
            "}": "rbrace",
        }

        self._tokens = []  # 保存token，格式：(token_type, token_value, line, column)
        self._line = 1
        self._column = 0
        self._code = ""

    def __str__(self):
        return f"Lexer"

    def tokenize_result(self):
        return self._tokens.copy()

    def code(self):
        return self._code

    def tokenize(self, code, tupleization=False):
        try:
            assert isinstance(code, str)
            self._code = code
            self._index = 0
            self._line = 1
            self._tokens.clear()

            while self._index < len(self._code):
                try:
                    self._tokenize_token()
                except Exception as e:
                    print(
                        f"Falied to tokenize at line {self._line}, column {self._column}: {e}"
                    )
                    sys.exit(1)
            
            if tupleization:
                for i in range(len(self._tokens)):
                    self._tokens[i] = self._tokens[i].tupleization()
        except Exception as e:
            print(f"Failed to tokenize: {e}")
            sys.exit(1)

    def _tokenize_token(self):
        start_index = self._index
        self._skip_whitespace()
        self._tokenize_comment()
        self._tokenize_keyword()
        self._tokenize_identifier()
        self._tokenize_number()
        self._tokenize_string()
        self._tokenize_character()
        self._tokenize_punctuator()
        if self._index == start_index:
            self._index += 1
            raise Exception(f'Invalid token "{self._code[self._index]}"')

    def _skip_whitespace(self):
        # 跳过空白字符
        while self._index < len(self._code) and self._code[self._index].isspace():
            if self._code[self._index] == "\n":
                self._line += 1
                self._column = 0
            else:
                self._column += 1
            self._index += 1

    def _tokenize_comment(self):
        # 处理注释
        if (
            self._index + 1 < len(self._code)
            and self._code[self._index : self._index + 2] == "/*"
        ):
            self._index += 2
            while (
                self._index + 1 < len(self._code)
                and self._code[self._index : self._index + 2] != "*/"
            ):
                if self._code[self._index] == "\n":
                    self._line += 1
                    self._column = 0
                else:
                    self._column += 1
                self._index += 1
            self._index += 2
        elif (
            self._index + 1 < len(self._code)
            and self._code[self._index : self._index + 2] == "//"
        ):
            self._index += 2
            while self._index < len(self._code) and self._code[self._index] != "\n":
                self._index += 1
            self._line += 1
            self._column = 0

    def _tokenize_keyword(self):
        # 处理关键字
        for keyword, token_type in self._keywords.items():
            if (
                self._index + len(keyword) <= len(self._code)
                and self._code[self._index : self._index + len(keyword)] == keyword
                and self._code[self._index + len(keyword)].isalnum() == False
                and self._code[self._index + len(keyword)] != "_"
            ):
                self._tokens.append(
                    Token(token_type, keyword, self._line, self._column)
                )
                self._index += len(keyword)
                self._column += len(keyword)

                if token_type == "include":
                    self._skip_whitespace()
                    self._tokenize_header()
                return

    def _tokenize_identifier(self):
        # 处理标识符
        if self._index < len(self._code) and (
            self._code[self._index].isalpha() or self._code[self._index] == "_"
        ):
            start = self._index
            while self._index < len(self._code) and (
                self._code[self._index].isalnum() or self._code[self._index] == "_"
            ):
                self._index += 1
            identifier = self._code[start : self._index]
            self._tokens.append(
                Token("identifier", identifier, self._line, self._column)
            )
            self._column += self._index - start

    def _tokenize_number(self):
        # 处理数字
        if self._index < len(self._code) and self._code[self._index].isdigit():
            start = self._index
            while self._index < len(self._code) and self._code[self._index].isdigit():
                self._index += 1
            if self._index < len(self._code) and self._code[self._index] == ".":
                self._index += 1
                while (
                    self._index < len(self._code) and self._code[self._index].isdigit()
                ):
                    self._index += 1
                self._tokens.append(
                    Token(
                        "number",
                        float(self._code[start : self._index]),
                        self._line,
                        self._column,
                    )
                )
            else:
                self._tokens.append(
                    Token(
                        "number",
                        int(self._code[start : self._index]),
                        self._line,
                        self._column,
                    )
                )
            self._column += self._index - start

    def _tokenize_string(self):
        # 处理字符串
        if self._index < len(self._code) and self._code[self._index] == '"':
            start = self._index
            self._index += 1
            while self._index < len(self._code) and self._code[self._index] != '"':
                if self._code[self._index] == "\\":
                    self._index += 2
                else:
                    self._index += 1
            if self._index == len(self._code):
                raise Exception("Invalid string")
            self._index += 1
            self._tokens.append(
                Token(
                    "string", self._code[start : self._index], self._line, self._column
                )
            )
            self._column += self._index - start

    def _tokenize_character(self):
        # 处理字符
        if self._index < len(self._code) and self._code[self._index] == "'":
            start = self._index
            self._index += 1
            if self._index < len(self._code) and self._code[self._index] == "\\":
                self._index += 2
            else:
                self._index += 1
            if self._index < len(self._code) and self._code[self._index] == "'":
                self._index += 1
                self._tokens.append(
                    Token(
                        "character",
                        self._code[start : self._index],
                        self._line,
                        self._column,
                    )
                )
                self._column += self._index - start
            else:
                raise Exception(
                    f'Invalid character "{self._code[start : self._index]}"'
                )

    def _tokenize_punctuator(self):
        # 处理标点符号
        for punctuator, token_type in self._punctuators.items():
            if (
                self._index + len(punctuator) <= len(self._code)
                and self._code[self._index : self._index + len(punctuator)]
                == punctuator
            ):
                self._tokens.append(
                    Token(token_type, punctuator, self._line, self._column)
                )
                self._index += len(punctuator)
                self._column += len(punctuator)
                return

    def _tokenize_header(self):
        # 处理头文件
        if self._index < len(self._code) and self._code[self._index] == "<":
            start = self._index
            self._index += 1
            while self._index < len(self._code) and self._code[self._index] != ">":
                if self._code[self._index] == "\n":
                    raise Exception("Invalid header")
                self._index += 1
            if self._index == len(self._code):
                raise Exception("Invalid header")
            self._index += 1
            self._tokens.append(
                Token("lt", self._code[start], self._line, self._column)
            )
            self._tokens.append(
                Token(
                    "header",
                    self._code[start + 1 : self._index - 1],
                    self._line,
                    self._column + 1,
                )
            )
            self._tokens.append(
                Token(
                    "gt",
                    self._code[self._index - 1],
                    self._line,
                    self._column + self._index - start - 1,
                )
            )
            self._column += self._index - start
        elif self._index < len(self._code) and self._code[self._index] == '"':
            start = self._index
            self._index += 1
            while self._index < len(self._code) and self._code[self._index] != '"':
                self._index += 1
            if self._index == len(self._code):
                raise Exception("Invalid header")
            self._index += 1
            self._tokens.append(
                Token(
                    "header", self._code[start : self._index], self._line, self._column
                )
            )
            self._column += self._index - start
        else:
            raise Exception("Invalid header")


if __name__ == "__main__":
    pass
