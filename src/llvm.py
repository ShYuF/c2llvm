from llvmlite import ir

import parser, lexer
import argparse, os

class IRGenerator:

    def __init__(self) -> None:
        self.module = None
        self.builderInst = None
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

    def isRealType(self, val):
        return isinstance(val.type, ir.IntType) or isinstance(val.type, ir.FloatType) or isinstance(val.type, ir.DoubleType)
    
    def builder(self):
        if self.builderInst == None:
            raise RuntimeError("operation now allowed outside of function bodies!")
        return self.builderInst

    def setBuilder(self, newBuilder):
        self.builderInst = newBuilder

    def assign(self, val, ptr):
        builder = self.builder()
        tar = ptr.type.pointee
        if tar == val.type:
            builder.store(val, ptr)
        elif isinstance(tar, ir.IntType):
            if isinstance(val.type, ir.IntType):
                val = builder.sext(val, ir.IntType(32))
                val = builder.trunc(val, tar)
                builder.store(val, ptr)
            elif isinstance(val.type, ir.FloatType) or isinstance(val.type, ir.DoubleType):
                val = builder.fptosi(val, tar)
                builder.store(val, ptr)
            else:
                raise RuntimeError("inapproriate types for assigning at line %d, column %d" % (chs[1]["line"], chs[1]["column"]))
        elif isinstance(tar, ir.FloatType) or isinstance(tar, ir.DoubleType):
            if isinstance(val.type, ir.IntType):
                val = builder.sitofp(val, tar)
                builder.store(val, ptr)
            elif isinstance(val.type, ir.FloatType) or isinstance(val.type, ir.DoubleType):
                val = builder.fpext(val, ir.DoubleType)
                val = builder.fptrunc(val, tar)
                builder.store(val, ptr)
            else:
                raise RuntimeError("inapproriate types for assigning at line %d, column %d" % (chs[1]["line"], chs[1]["column"]))
        else:
            raise RuntimeError("inapproriate types for assigning at line %d, column %d" % (chs[1]["line"], chs[1]["column"]))


    def getGroupItems(self, tree: dict, syms: dict):
        assert tree["type"] == "GROUP_ITEM"
        chs = tree["children"]
        if len(chs) == 1:
            return [self.codeGen(chs[0], syms)]
        else:
            return [self.codeGen(chs[0], syms)] + self.getGroupItems(chs[2], syms)

    def getParameters(self, params: dict):
        assert params["type"] == "PARAMETER"
        chs = params["children"]
        ret = [(self.getType(chs[0]["children"][0]), chs[1]["value"])]
        if len(chs) == 4:
            return ret + self.getParameters(chs[3])
        return ret

    def getIdentifier(self, node: dict, syms: dict):
        name = node["value"]
        if name not in syms:
            raise RuntimeError("identifier \"%s\" not found at line %d, column %d" % (name, node["line"], node["column"]))
        return syms[name]

    def codeGen(self, tree: dict, syms: dict):
        # print(tree["type"], ": builder =", builder)
        t = tree["type"]
        if "value" in tree:
            # non-terminals
            return None
        chs = tree["children"]
        if t == "FUNCTION_STMT":
            assert self.builderInst == None
            retType = self.codeGen(chs[0], syms)
            name = chs[1]["value"]
            if name in syms:
                raise RuntimeError("function name %s is already defined" % name)
            if len(chs) == 6:
                # argument list not empty
                params = self.getParameters(chs[3])
            else:
                params = []
            func = ir.Function(self.module, ir.FunctionType(ir.IntType(32), (t for t, _ in params)), name = name)
            syms[name] = func
            block = func.append_basic_block(name = "body")
            newBuilder = ir.IRBuilder(block)
            newSyms = syms.copy()
            for i, arg in enumerate(func.args):
                ptr = newBuilder.alloca(params[i][0])
                newBuilder.store(arg, ptr)
                newSyms[params[i][1]] = ptr
            # TODO add func.args to newSyms
            self.setBuilder(newBuilder)
            self.codeGen(chs[-1], newSyms)
            self.setBuilder(None)
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
            builder = self.builder()
            cond = self.codeGen(chs[2], syms)
            if len(chs) == 7:
                # ::= if lparen LINER_CODDITION rparen RESULT else RESULT
                with builder.if_else(cond) as (then, otherwise):
                    with then:
                        self.setBuilder(builder)
                        thenSyms = syms.copy()
                        self.codeGen(chs[4], thenSyms)
                    with otherwise:
                        self.setBuilder(builder)
                        elseSyms = syms.copy()
                        self.codeGen(chs[6], elseSyms)
                self.setBuilder(builder)
            else:
                # ::= if lparen LINER_CODDITION rparen RESULT
                with builder.if_then(cond):
                    self.setBuilder(builder)
                    thenSyms = syms.copy()
                    self.codeGen(chs[4], thenSyms)
                self.setBuilder(builder)
            return None
        elif t == "WHILE_STMT":
            # WHILE_STMT ::= while lparen LINER_CODDITION rparen RESULT
            oldBuilder = self.builder()
            condBlock = oldBuilder.append_basic_block("while")
            condBuilder = ir.IRBuilder(condBlock)
            bodyBlock = condBuilder.append_basic_block("body")
            bodyBuilder = ir.IRBuilder(bodyBlock)
            contBlock = bodyBuilder.append_basic_block("exit")
            contBuilder = ir.IRBuilder(contBlock)

            oldBuilder.branch(condBlock) # needed?

            self.setBuilder(condBuilder)
            cond = self.codeGen(chs[2], syms)
            condBuilder.cbranch(cond, bodyBlock, contBlock)

            self.setBuilder(bodyBuilder)
            newSyms = syms.copy()
            self.codeGen(chs[4], newSyms)
            bodyBuilder.branch(condBlock)

            self.setBuilder(contBuilder)
        elif t == "FOR_STMT":
# FOR_STMT -> for lparen FOR_INIT FOR_CONDITION FOR_ASSIGN rparen RESULT |      ; for 循环语句
#             for lparen FOR_INIT FOR_CONDITION rparen RESULT
            raise RuntimeError("FOR_STMT: TODO")
            oldBuilder = self.builder()
            initBlock = oldBuilder.append_basic_block("for_init")
            initBuilder = ir.IRBuilder(initBlock)
            condBlock = oldBuilder.append_basic_block("for_cond")
            condBuilder = ir.IRBuilder(condBlock)
            bodyBlock = condBuilder.append_basic_block("body")
            bodyBuilder = ir.IRBuilder(bodyBlock)
            contBlock = bodyBuilder.append_back_block("exit")
            contBuilder = ir.IRBuilder(contBlock)

            newSyms = syms.copy()
            oldBuilder.branch(condBlock) # needed?

            self.setBuilder(condBuilder)
            cond = self.codeGen(chs[2], syms)
            condBuilder.cbranch(cond, bodyBlock, contBlock)

            self.setBuilder(bodyBuilder)
            newSyms = syms.copy()
            self.codeGen(chs[4], newSyms)
            bodyBuilder.branch(condBlock)

            self.setBuilder(contBuilder)
        elif t == "ASSIGN_STMT":
            if chs[0]["type"] == "identifier":
                # ::= identifier assign VALUE_ITEM semicolon
                ptr = self.getIdentifier(chs[0], syms)
                val = self.codeGen(chs[2], syms)
                self.assign(val, ptr)

                return self.builder().load(ptr)

                # ::= ARRAY_ITEM assign VALUE_ITEM semicolon
            raise RuntimeError("\"ASSIGN_STMT\": TODO")
        elif t == "DECLARE_STMT":
            if self.builderInst != None:
                # local variable declaration
                builder = self.builder()
                if len(chs) == 3 and chs[1]["type"] == "identifier":
                    # ::= TYPE identifier semicolon
                    name = chs[1]["value"]
                    if name in syms:
                        raise RuntimeError("identifier \"%s\" (at line %d, column %d) is already defined" % (name, chs[1]["line"], chs[1]["column"]))
                    ptr = builder.alloca(self.getType(chs[0]["children"][0]), name = name)
                    syms[name] = ptr
                elif len(chs) == 5:
                    # ::= TYPE identifier assign VALUE_ITEM semicolon
                    name = chs[1]["value"]
                    if name in syms:
                        raise RuntimeError("identifier \"%s\" (at line %d, column %d) is already defined" % (name, chs[1]["line"], chs[1]["column"]))
                    ptr = builder.alloca(self.getType(chs[0]["children"][0]), name = name)
                    val = self.codeGen(chs[3], syms)
                    self.assign(val, ptr)
                    syms[name] = ptr
                elif len(chs) == 3 and chs[1]["type"] == "ARRAY_ITEM":
                    # ::= TYPE ARRAY_ITEM semicolon
                    # ARRAY_ITEM ::= identifier lbracket VALUE_ITEM rbracket
                    cchs = chs[1]["children"]
                    name = cchs[0]["value"]
                    if name in syms:
                        raise RuntimeError("identifier \"%s\" (at line %d, column %d) is already defined" % (name, cchs[0]["line"], cchs[0]["column"]))
                    ptr = builder.alloca(ir.ArrayType(self.getType(chs[0]["children"][0]), 1000))
                    # ptr = builder.alloca(self.getType(chs[0]["children"][0]), 1000, name = name)
                    syms[name] = ptr
                elif len(chs) == 6 and chs[1]["type"] == "ARRAY_ITEM":
                    # TYPE ARRAY_ITEM assign lbrace GROUP_ITEM rbrace
                    raise RuntimeError("not implemented")
                else:
                    raise RuntimeError("DECLARE_STMT: impossible branch")
            else:
                raise RuntimeError("global variable")
        elif t == "RETURN_STMT":
            val = self.findFirstChild(tree, "VALUE_ITEM")
            builder = self.builder()
            if val == None:
                # 无返回值，函数返回值应为 void
                builder.ret_void()
                return
            else:
                data = self.codeGen(val, syms)
                builder.ret(data)
                return
        elif t == "VALUE_ITEM":
            return self.codeGen(chs[0], syms)
        elif t == "continue":
            raise RuntimeError("\"continue\": TODO")
        elif t == "break":
            raise RuntimeError("\"break\": TODO")
        elif t == "EXPRESSION":
            # print("tree =", tree)
            if len(chs) == 1:
                # EXPRESSION ::= TREM
                return self.codeGen(chs[0], syms)
            elif chs[1]["type"] == "plus":
                builder = self.builder()
                lhs = self.codeGen(chs[0], syms)
                rhs = self.codeGen(chs[2], syms)
                return builder.add(lhs, rhs)
            elif chs[1]["type"] == "minus":
                builder = self.builder()
                lhs = self.codeGen(chs[0], syms)
                rhs = self.codeGen(chs[2], syms)
                return builder.sub(lhs, rhs)
            else:
                raise RuntimeError("EXPRESSION: impossible branch")
        elif t == "TERM":
            if len(chs) == 1:
                # TERM ::= FACTOR
                return self.codeGen(chs[0], syms)
            elif chs[1]["type"] == "times":
                builder = self.builder()
                lhs = self.codeGen(chs[0], syms)
                rhs = self.codeGen(chs[2], syms)
                return builder.mul(lhs, rhs)
            elif chs[1]["type"] == "divide":
                builder = self.builder()
                lhs = self.codeGen(chs[0], syms)
                rhs = self.codeGen(chs[2], syms)
                return builder.sdiv(lhs, rhs)
            else:
                raise RuntimeError("TERM: impossible branch")
        elif t == "FACTOR":
            if chs[0]["type"] == "NUMBER":
                return self.codeGen(chs[0], syms)
            elif chs[0]["type"] == "FUNCTION_CALL":
                return self.codeGen(chs[0], syms)
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
                builder = self.builder()
                operand = self.getIdentifier(chs[0], syms)
                if isinstance(operand.type.pointee, ir.ArrayType):
                    return operand
                else:
                    return builder.load(operand)
            elif chs[0]["type"] == "ARRAY_ITEM":
                ptr = self.codeGen(chs[0], syms)
                return self.builder().load(ptr)
            elif chs[0]["type"] == "lparen":
                return self.codeGen(chs[1], syms)
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
            if self.builderInst == None:
                raise RuntimeError("global function call is temporarily not allowed")
            else:
                builder = self.builder()
                funcName = chs[0]["value"]
                if len(chs) == 4:
                    args = self.getGroupItems(chs[2], syms)
                    # print("group =", chs[2], "args =", args)
                    for i, arg in enumerate(args):
                        # print(arg.type, isinstance(arg.type, ir.PointerType))
                        if isinstance(arg.type, ir.PointerType) and isinstance(arg.type.pointee, ir.ArrayType):
                            # 如果指向一个数组
                            args[i] = builder.bitcast(arg, ir.PointerType(arg.type.pointee.element))
                        elif isinstance(arg.type, ir.ArrayType):
                            # 如果是数组名
                            # print(arg)
                            args[i] = builder.gep(arg, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
                            args[i] = builder.bitcast(arg, ir.PointerType(arg.type.element))
                        # elif isinstance(arg, ir.GlobalVariable) and 
                if funcName not in syms:
                    raise RuntimeError("function \"%s\" not found at line %d, column %d" % (funcName, chs[0]["line"], chs[0]["column"]))
                else:
                    return builder.call(syms[funcName], args)
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
                val = eval(chs[0]["value"]).encode("utf-8")
                return ir.Constant(ir.IntType(8), int(val[0]))
            else:
                raise RuntimeException("CONSTANT: impossible branch")
        elif t == "TYPE":
            return self.getType(chs[0])
        elif t == "LINER_CODDITION": # CONDITION!!!
            if len(chs) == 2:
                # ::= logical_not LINER_CODDITION
                assert chs[0]["type"] == "logical_not"
                cond = self.codeGen(chs[1], syms)
                return self.builder().not_(cond)
            elif len(chs) == 3 and chs[1]["type"] == "logical_and":
                # ::= CONDITION logical_and LINER_CODDITION
                lhs = self.codeGen(chs[0], syms)
                rhs = self.codeGen(chs[2], syms)
                return self.builder().and_(lhs, rhs)
            elif len(chs) == 3 and chs[1]["type"] == "logical_or":
                # ::= CONDITION logical_or LINER_CODDITION
                lhs = self.codeGen(chs[0], syms)
                rhs = self.codeGen(chs[2], syms)
                return self.builder().or_(lhs, rhs)
            elif len(chs) == 1:
                # ::= CONDITION
                assert chs[0]["type"] == "CONDITION"
                return self.codeGen(chs[0], syms)
            else:
                raise RuntimeError("LINER_CONDITION: impossible branch")
        elif t == "CONDITION":
            lhs = self.codeGen(chs[0], syms)
            operand = "!="
            rhs = None
            builder = self.builder()
            if len(chs) == 1:
                rhs = ir.Constant(ir.IntType(32), 0)
            else:
                operand = chs[1]["value"]
                rhs = self.codeGen(chs[2], syms)
            if isinstance(lhs.type, ir.IntType) and isinstance(rhs.type, ir.IntType):
                # if both int
                lhs_ = builder.sext(lhs, ir.IntType(32))
                rhs_ = builder.sext(rhs, ir.IntType(32))
                return builder.icmp_signed(operand, lhs_, rhs_)
            elif self.isRealType(lhs) and self.isRealType(rhs):
                if isinstance(lhs.type, ir.IntType):
                    lhs = builder.sitofp(lhs, ir.DoubleType())
                else:
                    lhs = builder.fpext(lhs, ir.DoubleType())
                if isinstance(rhs.type, ir.IntType):
                    rhs = builder.sitofp(rhs, ir.DoubleType())
                else:
                    rhs = builder.fpext(rhs, ir.DoubleType())
                return builder.fcmp_ordered(operand, lhs, rhs)
            else:
                # print(lhs.type, rhs.type)
                raise RuntimeError("inappropriate types for comparing at line %d, column %d" % (chs[1]["line"], chs[1]["column"]))
        elif t == "ARRAY_ITEM":
            # ::= identifier lbracket VALUE_ITEM rbracket
            ptr = self.getIdentifier(chs[0], syms)
            idx = self.codeGen(chs[2], syms)
            if not isinstance(idx.type, ir.IntType):
                raise RuntimeError("invalid type for array subscripting at line %d, column %d" % (chs[1]["line"], chs[1]["column"]))
            ret = self.builder().gep(ptr, [ir.Constant(ir.IntType(32), 0), idx])
            return ret
        else:
            ret = None
            for ch in chs:
                ret = self.codeGen(ch, syms)
            return ret


    def generate(self, tree: dict) -> ir.Module:
        self.module = ir.Module(name = "undefined")
        self.builderInst = None
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
