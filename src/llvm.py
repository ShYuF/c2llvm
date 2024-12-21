from llvmlite import ir

import parser, lexer
import argparse, os

class IRGenerator:

    def __init__(self) -> None:
        self.module = None
        pass

    def findFirstChild(self, tree: dict, name: str):
        for child in tree["children"]:
            if child["type"] == name:
                return child
        return None

    def funcBodyGen(self, tree: dict, builder: ir.IRBuilder, args):
        t = tree["type"]
        if "value" in tree:
            # non-terminals
            return
        chs = tree["children"]
        if t == "RETURN_STMT":
            val = self.findFirstChild(tree, "VALUE_ITEM")
            if val == None:
                # 无返回值，函数返回值应为 void
                builder.ret_void()
                return
            else:
                data = self.codeGen(val)
                builder.ret(data)
                return
        else:
            for ch in chs:
                self.funcBodyGen(ch, builder, args)

    def codeGen(self, tree: dict):
        t = tree["type"]
        if "value" in tree:
            # non-terminals
            return None
        chs = tree["children"]
        if t == "DECLARE_STMT":
            pass
        elif t == "FUNCTION_STMT":
            retType = self.codeGen(chs[0])
            name = chs[1]["value"]
            func = ir.Function(self.module, ir.FunctionType(ir.IntType(32), ()), name = name)
            block = func.append_basic_block(name = "body")
            builder = ir.IRBuilder(block)
            self.funcBodyGen(chs[-1], builder, func.args)
        elif t == "HEADER_STMT":
            pass
        elif t == "IF_STMT":
            pass
        elif t == "WHILE_STMT":
            pass
        elif t == "FOR_STMT":
            pass
        elif t == "ASSIGN_STMT":
            pass
        elif t == "DECLARE_STMT":
            pass
        elif t == "RETURN_STMT":
            pass
        elif t == "VALUE_ITEM":
            return self.codeGen(chs[0])
        elif t == "continue":
            pass
        elif t == "break":
            pass
        elif t == "EXPRESSION":
            if len(chs) == 1:
                # EXPRESSION ::= TREM
                return self.codeGen(chs[0])
            elif chs[1]["value"] == "plus":
                pass
            elif chs[1]["value"] == "minus":
                pass
            else:
                raise RuntimeError("EXPRESSION: impossible branch")
        elif t == "TERM":
            if len(chs) == 1:
                # TERM ::= FACTOR
                return self.codeGen(chs[0])
            elif chs[1]["value"] == "times":
                pass
            elif chs[1]["value"] == "divide":
                pass
            else:
                raise RuntimeError("TERM: impossible branch")
        elif t == "FACTOR":
            if chs[0]["type"] == "NUMBER":
                return self.codeGen(chs[0])
            else:
                raise RuntimeError("FACTOR: impossible branch")
        elif t == "NUMBER":
            if len(chs) == 1 and chs[0]["type"] == "number":
                val = chs[0]["value"]
                if type(val) == int:
                    return ir.Constant(ir.IntType(32), val)
                elif type(val) == float:
                    return ir.Constant(ir.FloatType(), val)
                else:
                    raise RuntimeError("NUMBER value: impossible branch")
            elif len(chs) == 2 and chs[0]["type"] == "minus" and chs[1]["type"] == "number":
                # NUMBER ::= minus number
                pass
            else:
                raise RuntimeError("NUMBER: impossible branch")
        elif t == "TYPE":
            val = chs[0]["value"]
            if val == "int":
                return ir.IntType(32)
            elif val == "float":
                return ir.FloatType()
            elif val == "double":
                return ir.DoubleType()
            elif val == "char":
                return ir.IntType(8)
            elif val == "void":
                return ir.VoidType()
            else:
                raise RuntimeError("invalid type \"%s\" at line %d, col %d" % (val, chs[0]["line"], chs[0]["column"]))
        else:
            ret = None
            for ch in chs:
                ret = self.codeGen(ch)
            return ret


    def generate(self, tree: dict) -> ir.Module:
        self.module = ir.Module(name = "undefined")
        self.codeGen(tree)
        # # Create some useful types
        # double = ir.DoubleType()
        # fnty = ir.FunctionType(double, (double, double))

        # # Create an empty module...
        # module = ir.Module(name=__file__)
        # # and declare a function named "fpadd" inside it
        # func = ir.Function(module, fnty, name="fpadd")

        # # Now implement the function
        # block = func.append_basic_block(name="entry")
        # builder = ir.IRBuilder(block)
        # a, b = func.args
        # result = builder.fadd(a, b, name="res")
        # builder.ret(result)

        return self.module

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Parser")
    # 两组
    group = arg_parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-t", "--test", action="store_true", help="使用样例程序测试语法分析器"
    )

    group.add_argument("-i", "--input", type=str, help="输入文件路径")
    arg_parser.add_argument("-o", "--output", type=str, help="输出文件路径")

    args = arg_parser.parse_args()
    if args.test:
        parser.test_parser()
    else:
        if (
            not args.input
            or not os.path.exists(args.input)
            or not args.input.endswith(".c")
        ):
            print("Please input correct file path and output path")
            exit(1)
        lexer_instance = lexer.Lexer()
        parser_instance = parser.Parser()
        with open(args.input, "r", encoding="utf-8") as file:
            content = file.read()
        lexer_instance.tokenize(content, True)
        tokens = lexer_instance.tokenize_result()
        syntax_tree = parser_instance.parse(tokens)

        generator_instance = IRGenerator()

        if not args.output:
            args.output = args.input.replace(".c", ".ll")

        with open(args.output, "w") as file:
            print(generator_instance.generate(syntax_tree), file = file)
