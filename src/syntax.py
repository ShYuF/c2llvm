# 保存 C 语法
# /src/syntax.py
rules = {
    "PROGRAM": {
        "name": "PROGRAM",
        "rules": [
            [
                "OUTER_STMT",
                "OUTER_SUB_PROGRAM"
            ],
            [
                "OUTER_STMT"
            ]
        ]
    },
    "OUTER_SUB_PROGRAM": {
        "name": "",
        "rules": [
            [
                "OUTER_STMT",
                "OUTER_SUB_PROGRAM"
            ],
            [
                "OUTER_STMT"
            ]
        ]
    },
    "OUTER_STMT": {
        "name": "OUTER_STMT",
        "rules": [
            [
                "HEADER_STMT"
            ],
            [
                "DEFINE_STMT"
            ],
            [
                "DECLARE_STMT"
            ],
            [
                "FUNCTION_STMT"
            ]
        ]
    },
    "INNER_SUB_PROGRAM": {
        "name": "",
        "rules": [
            [
                "INNER_STMT",
                "INNER_SUB_PROGRAM"
            ],
            [
                "INNER_STMT"
            ]
        ]
    },
    "INNER_STMT": {
        "name": "INNER_STMT",
        "rules": [
            [
                "IF_STMT"
            ],
            [
                "WHILE_STMT"
            ],
            [
                "FOR_STMT"
            ],
            [
                "ASSIGN_STMT"
            ],
            [
                "DECLARE_STMT"
            ],
            [
                "VALUE_ITEM",
                "semicolon"
            ],
            [
                "RETURN_STMT"
            ],
            [
                "continue",
                "semicolon"
            ],
            [
                "break",
                "semicolon"
            ],
        ]
    },
    "HEADER_STMT": {
        "name": "HEADER_STMT",
        "rules": [
            [
                "include",
                "lt",
                "header",
                "gt"
            ]
        ]
    },
    "DEFINE_STMT": {
        "name": "DEFINE_STMT",
        "rules": [
            [
                "define",
                "identifier",
                "VALUE_ITEM",
            ]
        ]
    },
    "IF_STMT": {
        "name": "IF_STMT",
        "rules": [
            [
                "if",
                "lparen",
                "LINER_CODDITION",
                "rparen",
                "RESULT",
                "else",
                "RESULT"
            ],
            [
                "if",
                "lparen",
                "LINER_CODDITION",
                "rparen",
                "RESULT"
            ],
        ]
    },
    "RESULT": {
        "name": "",
        "rules": [
            [
                "BLOCK"
            ],
            [
                "INNER_STMT"
            ]
        ]
    },
    "WHILE_STMT": {
        "name": "WHILE_STMT",
        "rules": [
            [
                "while",
                "lparen",
                "LINER_CODDITION",
                "rparen",
                "RESULT"
            ]
        ]
    },
    "FOR_STMT": {
        "name": "FOR_STMT",
        "rules": [
            [
                "for",
                "lparen",
                "FOR_INIT",
                "FOR_CONDITION",
                "ASSIGN_STMT",
                "rparen",
                "RESULT"
            ],
            [
                "for",
                "lparen",
                "FOR_INIT",
                "FOR_CONDITION",
                "rparen",
                "RESULT"
            ]
        ]
    },
    "FOR_INIT": {
        "name": "FOR_INIT",
        "rules": [
            [
                "ASSIGN_STMT",
                "semicolon"
            ],
            [
                "DECLARE_STMT",
                "semicolon"
            ],
            [
                "semicolon"
            ]
        ]
    },
    "FOR_CONDITION": {
        "name": "FOR_CONDITION",
        "rules": [
            [
                "LINER_CODDITION",
                "semicolon"
            ],
            [
                "semicolon"
            ]
        ]
    },
    "ASSIGN_STMT": {
        "name": "ASSIGN_STMT",
        "rules": [
            [
                "identifier",
                "assign",
                "VALUE_ITEM",
                "semicolon"
            ],
            [
                "ARRAY_ITEM",
                "assign",
                "VALUE_ITEM",
                "semicolon"
            ]
        ]
    },
    "DECLARE_STMT": {
        "name": "DECLARE_STMT",
        "rules": [
            [
                "TYPE",
                "identifier",
                "semicolon"
            ],
            [
                "TYPE",
                "identifier",
                "assign",
                "VALUE_ITEM",
                "semicolon"
            ],           
            [
                "TYPE",
                "ARRAY_ITEM",
                "semicolon"
            ],
            [
                "TYPE",
                "ARRAY_ITEM",
                "assign",
                "lbrace",
                "GROUP_ITEM",
                "rbrace",
            ],
        ]
    },
    "GROUP_ITEM": {
        "name": "GROUP_ITEM",
        "rules": [
            [
                "VALUE_ITEM",
                "comma",
                "GROUP_ITEM"
            ],
            [
                "VALUE_ITEM",
            ],
        ]
    },
    "CONSTANT": {
        "name": "CONSTANT",
        "rules": [
            [
                "string"
            ],
            [
                "character"
            ]
        ]
    },
    "TYPE": {
        "name": "TYPE",
        "rules": [
            [
                "int"
            ],
            [
                "float"
            ],
            [
                "double"
            ],
            [
                "char"
            ],
            [
                "void"
            ]
        ]
    },
    "EXPRESSION": {
        "name": "EXPRESSION",
        "rules": [
            [
                "TERM",
                "plus",
                "EXPRESSION"
            ],
            [
                "TERM",
                "minus",
                "EXPRESSION"
            ],
            [
                "TERM"
            ]
        ]
    },
    "TERM": {
        "name": "TERM",
        "rules": [
            [
                "FACTOR",
                "times",
                "TERM"
            ],
            [
                "FACTOR",
                "divide",
                "TERM"
            ],
            [
                "FACTOR"
            ]
        ]
    },      
    "FACTOR": {
        "name": "FACTOR",
        "rules": [
            [
                "BIT_OP",
                "identifier"
            ],
            [
                "BIT_OP",
                "ARRAY_ITEM"
            ],
            [
                "identifier"
            ],
            [
                "ARRAY_ITEM"
            ],
            [
                "NUMBER"
            ],
            [
                "FUNCTION_CALL"
            ],
            [
                "lparen",
                "EXPRESSION",
                "rparen"
            ]
        ]
    },
    "ARRAY_ITEM": {
        "name": "",
        "rules": [
            [
                "identifier",
                "lbracket",
                "VALUE_ITEM",
                "rbracket"
            ]
        ]
    },
    "FUNCTION_CALL": {
        "name": "FUNCTION_CALL",
        "rules": [
            [
                "identifier",
                "lparen",
                "GROUP_ITEM",
                "rparen"
            ],
            [
                "identifier",
                "lparen",
                "rparen"
            ]
        ]
    },
    "VALUE_ITEM": {
        "name": "",
        "rules": [
            [
                "EXPRESSION"
            ],
            [
                "CONSTANT"
            ],
        ]
    },
    "BIT_OP": {
        "name": "",
        "rules": [
            [
                "bitwise_and"
            ],
            [
                "bitwise_or"
            ],
            [
                "bitwise_xor"
            ],
            [
                "bitwise_not"
            ],
        ]
    },
    "LINER_CODDITION": {
        "name": "",
        "rules": [
            [
                "logical_not",
                "LINER_CODDITION"
            ],
            [
                "CONDITION",
                "logical_and",
                "LINER_CODDITION"
            ],
            [
                "CONDITION",
                "logical_or",
                "LINER_CODDITION"
            ],
            [
                "CONDITION"
            ],
        ]
    },
    "CONDITION": {
        "name": "CONDITION",
        "rules": [
            [
                "VALUE_ITEM",
                "lt",
                "VALUE_ITEM",
            ],
            [
                "VALUE_ITEM",
                "le",
                "VALUE_ITEM",
            ],
            [
                "VALUE_ITEM",
                "gt",
                "VALUE_ITEM",
            ],
            [
                "VALUE_ITEM",
                "ge",
                "VALUE_ITEM",
            ],
            [
                "VALUE_ITEM",
                "eq",
                "VALUE_ITEM",
            ],
            [
                "VALUE_ITEM",
                "neq",
                "VALUE_ITEM",
            ],
            [
                "VALUE_ITEM",
            ]
        ]
    },
    "BLOCK": {
        "name": "BLOCK",
        "rules": [
            [
                "lbrace",
                "INNER_SUB_PROGRAM",
                "rbrace"
            ]
        ]
    },
    "FUNCTION_STMT": {
        "name": "FUNCTION_STMT",
        "rules": [
            [
                "TYPE",
                "identifier",
                "lparen",
                "PARAMETER",
                "rparen",
                "BLOCK"
            ],
            [
                "TYPE",
                "identifier",
                "lparen",
                "rparen",
                "BLOCK"
            ]
        ]
    },
    "PARAMETER": {
        "name": "PARAMETER",
        "rules": [
            [
                "TYPE",
                "identifier",
                "comma",
                "PARAMETER"
            ],
            [
                "TYPE",
                "identifier"
            ]
        ]
    },
    "RETURN_STMT": {
        "name": "RETURN_STMT",
        "rules": [
            [
                "return",
                "VALUE_ITEM",
                "semicolon"
            ],
            [
                "return",
                "semicolon"
            ]
        ]
    },
    "NUMBER": {
        "name": "NUMBER",
        "rules": [
            [
                "number"
            ],
            [
                "minus",
                "number"
            ]
        ]
    }
}

entry = "PROGRAM"

end = "#"

helper = {
    "PROGRAM": "程序的入口点",
    "OUTER_SUB_PROGRAM": "外部子程序",
    "OUTER_STMT": "外部语句",
    "INNER_SUB_PROGRAM": "内部子程序",
    "INNER_STMT": "内部语句",
    "HEADER_STMT": "头文件语句",
    "DEFINE_STMT": "宏定义语句",
    "IF_STMT": "条件语句",
    "RESULT": "条件或循环的结果块",
    "WHILE_STMT": "while 循环语句",
    "FOR_STMT": "for 循环语句",
    "FOR_INIT": "for 循环初始化",
    "FOR_CONDITION": "for 循环条件",
    "ASSIGN_STMT": "赋值语句",
    "DECLARE_STMT": "声明语句",
    "GROUP_ITEM": "组项",
    "CONSTANT": "常量",
    "TYPE": "数据类型",
    "EXPRESSION": "表达式",
    "TERM": "项",
    "FACTOR": "因子",
    "FUNCTION_CALL": "函数调用",
    "VALUE_ITEM": "值项",
    "CONDITION": "条件",
    "BLOCK": "代码块",
    "FUNCTION_STMT": "函数声明语句",
    "PARAMETER": "参数",
    "RETURN_STMT": "返回语句",
    "LINER_CODDITION": "线性条件",
    "BIT_OP": "位运算符",
    "NUMBER": "数字",
    "ARRAY_ITEM": "数组项"
}