import json
import lexer
import parser  # 假设您的 Parser 类保存在 parser.py 中

if __name__ == "__main__":
    lexer = lexer.Lexer()
    parser = parser.Parser()

    # 解析第一个C程序
    path = r"../in/palindrome.c"
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    lexer.tokenize(content, True)
    tokens = lexer.tokenize_result()
    syntax_tree = parser.parse(tokens)
    # 将语法树写入JSON文件
    with open("out1.json", "w", encoding="utf-8") as f:
        json.dump(syntax_tree, f, indent=4, ensure_ascii=False)

    # 解析第二个C程序
    path = r"../in/doubleBubbleSort.c"
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    lexer.tokenize(content, True)
    tokens = lexer.tokenize_result()
    syntax_tree = parser.parse(tokens)
    # 将语法树写入JSON文件
    with open("out2.json", "w", encoding="utf-8") as f:
        json.dump(syntax_tree, f, indent=4, ensure_ascii=False)