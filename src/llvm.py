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

    def getType(self, typeItem: dict):
        val = typeItem["value"]
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
            raise RuntimeError("invalid type \"%s\" at line %d, col %d" % (val, typeItem["line"], typeItem["column"]))

    def getGroupItems(self, tree: dict, syms: dict, builder = None):
        assert tree["type"] == "GROUP_ITEM"
        chs = tree["children"]
        if len(chs) == 1:
            return [self.codeGen(chs[0], syms, builder = builder)]
        else:
            return [self.codeGen(chs[0], syms, builder = builder)] + self.getGroupItems(chs[2], syms, builder = builder)

    def getIdentifier(self, node: dict, syms: dict):
        name = node["value"]
        if name not in syms:
            raise RuntimeError("identifier \"%s\" not found at line %d, column %d" % (name, node["line"], node["column"]))
        return syms[name]

    def codeGen(self, tree: dict, syms: dict, builder = None):
        # print(tree["type"], ": builder =", builder)
        t = tree["type"]
        if "value" in tree:
            # non-terminals
            return None
        chs = tree["children"]
        if t == "FUNCTION_STMT":
            assert builder == None
            retType = self.codeGen(chs[0], syms)
            name = chs[1]["value"]
            func = ir.Function(self.module, ir.FunctionType(ir.IntType(32), ()), name = name)
            block = func.append_basic_block(name = "body")
            newBuilder = ir.IRBuilder(block)
            newSyms = syms.copy()
            # TODO add func.args to newSyms
            self.codeGen(chs[-1], newSyms, builder = newBuilder)
        elif t == "HEADER_STMT":
            header = chs[2]["value"]
            if header == "stdio.h":
                # define prototypes for scanf and printf (for simplicity)
                # ir.Function(self.module, ir.FunctionType(ir.IntType(32), (ir.PointerType(ir.IntType(8))), var_arg = True), name = "scanf")
                # ir.Function(self.module, ir.FunctionType(ir.IntType(32), (ir.PointerType(ir.IntType(8))), var_arg = True), name = "printf")
                if "scanf" in syms:
                    raise RuntimeError("\"scanf\" redefined")
                if "printf" in syms:
                    raise RuntimeError("\"printf\" redefined")
                syms["scanf"] = ir.Function(self.module, ir.FunctionType(ir.IntType(32), (ir.PointerType(ir.IntType(8)),), var_arg = True), name = "scanf")
                syms["printf"] = ir.Function(self.module, ir.FunctionType(ir.IntType(32), (ir.PointerType(ir.IntType(8)),), var_arg = True), name = "printf")
            else:
                # other headers not allowed
                raise RuntimeError("header not found: \"%s\"" % header)
        elif t == "IF_STMT":
            pass
        elif t == "WHILE_STMT":
            pass
        elif t == "FOR_STMT":
            pass
        elif t == "ASSIGN_STMT":
            pass
        elif t == "DECLARE_STMT":
            if builder != None:
                # local variable declaration
                if len(chs) == 3:
                    name = chs[1]["value"]
                    if name in syms:
                        raise RuntimeError("identifier \"%s\" is already defined at line %d, column %d" % (name, chs[1]["line"], chs[1]["column"]))
                    ptr = builder.alloca(self.getType(chs[0]["children"][0]), name = name)
                    syms[name] = ptr
                else:
                    pass
        elif t == "RETURN_STMT":
            val = self.findFirstChild(tree, "VALUE_ITEM")
            if val == None:
                # 无返回值，函数返回值应为 void
                builder.ret_void()
                return
            else:
                data = self.codeGen(val, syms, builder = builder)
                builder.ret(data)
                return
        elif t == "VALUE_ITEM":
            return self.codeGen(chs[0], syms, builder = builder)
        elif t == "continue":
            pass
        elif t == "break":
            pass
        elif t == "EXPRESSION":
            if len(chs) == 1:
                # EXPRESSION ::= TREM
                return self.codeGen(chs[0], syms, builder = builder)
            elif chs[1]["type"] == "plus":
                if builder == None:
                    raise RuntimeError("operation not supported outside function body!")
                lhs = self.codeGen(chs[0], syms, builder = builder)
                rhs = self.codeGen(chs[2], syms, builder = builder)
                return builder.add(lhs, rhs)
            elif chs[1]["type"] == "minus":
                pass
            else:
                raise RuntimeError("EXPRESSION: impossible branch")
        elif t == "TERM":
            if len(chs) == 1:
                # TERM ::= FACTOR
                return self.codeGen(chs[0], syms, builder = builder)
            elif chs[1]["type"] == "times":
                pass
            elif chs[1]["type"] == "divide":
                pass
            else:
                raise RuntimeError("TERM: impossible branch")
        elif t == "FACTOR":
            if chs[0]["type"] == "NUMBER":
                return self.codeGen(chs[0], syms, builder = builder)
            elif chs[0]["type"] == "FUNCTION_CALL":
                return self.codeGen(chs[0], syms, builder = builder)
            elif chs[0]["type"] == "BIT_OP" and chs[1]["type"] == "identifier":
                # FACTOR ::= BIT_OP identifier
                bitOp = chs[0]["children"][0]["type"]
                operand = self.getIdentifier(chs[1], syms)
                if bitOp == "bitwise_and":
                    # address op
                    return operand
                else:
                    raise RuntimeError("FACTOR BIT_OP: impossible branch")
            elif chs[0]["type"] == "identifier":
                if builder == None:
                    raise RuntimeError("operation not allowed outside function body")
                operand = self.getIdentifier(chs[0], syms)
                return builder.load(operand)
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
        elif t == "FUNCTION_CALL":
            if builder == None:
                raise RuntimeError("global function call is temporarily not allowed")
            else:
                funcName = chs[0]["value"]
                if len(chs) == 4:
                    args = self.getGroupItems(chs[2], syms, builder = builder)
                    for i, arg in enumerate(args):
                        # print(arg.type, isinstance(arg.type, ir.PointerType))
                        if isinstance(arg.type, ir.PointerType) and isinstance(arg.type.pointee, ir.ArrayType):
                            # 如果是一个数组名
                            args[i] = builder.bitcast(arg, ir.PointerType(arg.type.pointee.element))
                        # elif isinstance(arg, ir.GlobalVariable) and 
                if funcName not in syms:
                    raise RuntimeError("function \"%s\" not found at line %d, column %d" % (funcName, chs[0]["line"], chs[0]["column"]))
                else:
                    builder.call(syms[funcName], args)
        elif t == "CONSTANT":
            if chs[0]["type"] == "string":
                val = eval(chs[0]["value"]) + "\0"
                tmpName = self.module.get_unique_name()
                ptr = ir.GlobalVariable(self.module, ir.ArrayType(ir.IntType(8), len(val)), tmpName)
                ptr.global_constant = True
                ptr.unnamed_addr = True
                ptr.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(val)), bytearray(val.encode("utf-8")))
                return ptr
                # return ir.Constant(ir.ArrayType(ir.IntType(8), len(val)), val)
            elif chs[0]["type"] == "character":
                pass
            else:
                raise RuntimeException("CONSTANT: impossible branch")
        elif t == "TYPE":
            return self.getType(chs[0])
        else:
            ret = None
            for ch in chs:
                ret = self.codeGen(ch, syms, builder = builder)
            return ret


    def generate(self, tree: dict) -> ir.Module:
        self.module = ir.Module(name = "undefined")
        self.codeGen(tree, {})
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
