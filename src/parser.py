# /src/parser.py

import argparse
import json
import lexer
import os
import syntax


class Parser:
    """
    LR(1)语法分析器
    """

    def __init__(self) -> None:
        """
        初始化语法分析器
        """
        try:
            # 读取语法规则或直接传入规则
            self._rules = syntax.rules
            self._entry = syntax.entry
            self._lr1_end = syntax.end  # LR(1)文法结束符

            # 自检
            state, info = self._self_check()
            if not state:
                raise Exception(info)

            # 求LR(1)拓广文法、符号名称和符号集（Vn ∪ Vt）
            self._lr1_rules, self._lr1_sign_name, self._lr1_signs = (
                self._cal_lr1_rules()
            )

            # 求LR(1)项目集规范族和GO函数
            self._lr1_clan, self._lr1_go = self._cal_lr1_clan()

            # 求LR(1)分析表
            self._lr1_table = self._cal_lr1_table()

            # 初始化状态栈和符号栈
            self._stack: list = []  # 确定下推自动机的状态栈，内部结构：(状态, 符号)
        except Exception as e:
            print(f"Error occurred when initializing parser: {e}")
            exit(1)

    def _self_check(self) -> tuple[bool, str]:
        """
        自检
        """
        try:
            # 检查规则
            assert isinstance(self._rules, dict), "Rules Error!"
            for rule in self._rules.values():
                assert isinstance(rule, dict), "Rules Error!"
                assert "name" in rule.keys(), "Rules Error!"
                assert "rules" in rule.keys(), "Rules Error!"
                assert isinstance(rule["name"], str), "Rules Error!"
                assert isinstance(rule["rules"], list), "Rules Error!"
                for r in rule["rules"]:
                    assert isinstance(r, list), "Rules Error!"
                    for i in r:
                        assert isinstance(i, str), "Rules Error!"

            # 检查入口
            assert isinstance(self._entry, str), "Entry Error!"
            assert self._entry in self._rules.keys(), "Entry Error!"

            return True, "OK"
        except Exception as e:
            return False, e

    def _cal_lr1_rules(self) -> tuple[list, dict, set]:
        """
        求拓广文法

        :return: LR(1)规则、LR(1)文法符号名称和LR(1)文法符号集
        """
        lr1_rules = []  # LR(1)规则，内部元素结构：[产生式左部，产生式右部]
        lr1_sign_name = {}  # LR(1)文法符号名称（非终结符）
        lr1_signs = set()  # LR(1)文法符号集（Vn ∪ Vt）
        lr1_signs.add("ENTRY")
        lr1_signs.add(self._lr1_end)
        lr1_sign_name["ENTRY"] = ""  # 保持 ENTRY 的类型名称为空

        for key in self._rules.keys():
            lr1_signs.add(key)
            for rule in self._rules[key]["rules"]:
                for i in rule:
                    lr1_signs.add(i)

        lr1_rules.append(["ENTRY", [self._entry]])
        self._entry = "ENTRY"
        for key in self._rules.keys():
            lr1_sign_name[key] = self._rules[key]["name"] or key  # 确保名称不为空
            for rule in self._rules[key]["rules"]:
                lr1_rules.append([key, rule.copy()])
        return lr1_rules, lr1_sign_name, lr1_signs

    def _cal_lr1_clan(self) -> tuple[list, dict]:
        """
        求LR(1)项目集规范族

        :return: 项目集规范族和GO函数表（不是GOTO表）
        """

        # 先求项目集的FIRST集
        def _cal_first(rules: list, sign_name: dict) -> dict:
            """
            求FIRST集
            """
            _first = {name: set() for name in sign_name.keys()}

            while True:
                flag: bool = False  # 更新标志
                for rule in rules:
                    key: str = rule[0]
                    right_signs: list = rule[1]
                    # 如果是非终结符
                    if right_signs[0] in sign_name.keys():
                        before_len = len(_first[key])
                        _first[key] = _first[key].union(_first[right_signs[0]])
                        after_len = len(_first[key])
                        if before_len != after_len:
                            flag = True
                    # 如果是终结符
                    else:
                        if right_signs[0] not in _first[key]:
                            _first[key].add(right_signs[0])
                            flag = True

                if not flag:
                    break

            # set转换为list
            # for key in _first.keys():
            #     _first[key] = list(_first[key])
            return _first

        _first = _cal_first(self._lr1_rules, self._lr1_sign_name)

        # 再求项目集的FOLLOW集
        def _cal_follow(
            rules: list, sign_name: dict, first: dict, end_sign: str
        ) -> dict:
            """
            求FOLLOW集
            """
            _follow = {name: set() for name in sign_name.keys()}
            _follow["ENTRY"].add(end_sign)
            while True:
                flag: bool = False
                for rule in rules:
                    key: str = rule[0]
                    right_signs: list = rule[1]
                    for i in range(len(right_signs) - 1):
                        if right_signs[i] in sign_name.keys():
                            before_len = len(_follow[right_signs[i]])
                            # 判断右侧第一个符号是否是非终结符
                            if right_signs[i + 1] in sign_name.keys():
                                _follow[right_signs[i]] = _follow[right_signs[i]].union(
                                    first[right_signs[i + 1]]
                                )
                            # 如果是终结符
                            else:
                                if right_signs[i + 1] not in _follow[right_signs[i]]:
                                    _follow[right_signs[i]].add(right_signs[i + 1])
                            after_len = len(_follow[right_signs[i]])

                            if before_len != after_len:
                                flag = True

                    # 处理最后一个符号
                    if right_signs[-1] in sign_name.keys():
                        before_len = len(_follow[right_signs[-1]])
                        _follow[right_signs[-1]] = _follow[right_signs[-1]].union(
                            _follow[key]
                        )
                        after_len = len(_follow[right_signs[-1]])
                        if before_len != after_len:
                            flag = True

                if not flag:
                    break

            # set转换为list
            # for key in _follow.keys():
            #     _follow[key] = list(_follow[key])
            return _follow

        _follow = _cal_follow(
            self._lr1_rules, self._lr1_sign_name, _first, self._lr1_end
        )

        # 求项目集规范族
        def _cal_clan(
            rules: list, sign_name: dict, signs: list, first: dict, follow: dict
        ) -> tuple[list, dict]:
            """
            求项目集规范族
            """

            def _cal_closure(item_list: list) -> list:
                """
                求项目集闭包

                :param item_list: 项目集
                    其中 item 结构：[产生式左部, 产生式右部, 点的位置, 展望符号集]
                :return: 项目集的闭包
                """
                closure = item_list.copy()
                while True:
                    flag = False
                    for item in closure:
                        right_signs: list = item[1]  # 产生式右部
                        dot_index: int = item[2]  # 点的位置，即产生式右部的第几个符号
                        outlooks: set = item[3]  # 展望符号集
                        # 如果点的位置在产生式右部的末尾，则跳过
                        # 或者点的位置的符号是终结符，跳过
                        if (
                            dot_index < len(right_signs)
                            and right_signs[dot_index] in sign_name.keys()
                        ):
                            # 对于形如 A -> α.Bβ, a 的产生式，将 B -> .γ, b 加入闭包，其中 b ∈ FIRST(βa)
                            # 如果点的位置是产生式右部的最后一个符号，那么 FIRST(βa) = FOLLOW(A)
                            first_beta_a = set()
                            if dot_index + 1 == len(right_signs):
                                first_beta_a = first_beta_a.union(outlooks.copy())
                            else:
                                next_sign: str = right_signs[dot_index + 1]
                                # 如果下一个符号是终结符，那么 FIRST(βa) = {next_sign}
                                if next_sign not in sign_name.keys():
                                    first_beta_a.add(next_sign)
                                # 否则，FIRST(βa) = FIRST(β)
                                else:
                                    first_beta_a = first_beta_a.union(
                                        first[next_sign].copy()
                                    )
                            for rule in rules:
                                # 如果找到的产生式左部等于点右部的第一个符号
                                if rule[0] == right_signs[dot_index]:
                                    new_item = [
                                        rule[0],
                                        rule[1].copy(),
                                        0,
                                        first_beta_a.copy(),
                                    ]
                                    if new_item not in closure:
                                        closure.append(new_item)
                                        flag = True
                    if not flag:
                        break

                return closure

            def _go(item_list: list, sign: str) -> list:
                """
                求项目集的后继
                    GO(I, X) = CLOSURE(J)，
                    其中 J = {[A -> αX.β , a] | [A -> α.Xβ , a] ∈ I}

                :param item_list: 项目集
                    其中 item 结构：[产生式左部, 产生式右部, 点的位置, 展望符号集]
                :param sign: 符号
                :return: 项目集的后继
                """
                go = []
                for item in item_list:
                    key: str = item[0]
                    right_signs: list = item[1]
                    dot_index: int = item[2]
                    outlooks: set = item[3]
                    if dot_index < len(right_signs) and right_signs[dot_index] == sign:
                        new_item = [
                            key,
                            right_signs.copy(),
                            dot_index + 1,
                            outlooks.copy(),
                        ]
                        if new_item not in go:
                            go.append(new_item)
                return _cal_closure(go)

            clan = []  # 项目集规范族
            go_rules: dict = (
                {}
            )  # GO函数的转移规则，内部元素结构：(项目集索引, 符号 ): 转移项目集索引

            # 求初始项目集闭包
            initial_item_list: list = [
                [rules[0][0], rules[0][1].copy(), 0, follow["ENTRY"].copy()]
            ]
            initial_closure = _cal_closure(initial_item_list)
            clan.append(initial_closure)

            index = 0  # 枚举的项目集索引
            length = 1  # 项目集规范族的长度
            while index < length:
                # 对于每个项目集，枚举X
                for sign in signs:
                    go_item = _go(clan[index], sign)
                    if go_item:
                        if go_item not in clan:
                            clan.append(go_item)
                            go_rules[(index, sign)] = length
                            length += 1
                        else:
                            go_rules[(index, sign)] = clan.index(go_item)
                        # 记录日志（测试用）
                        # with open("log.txt", "a") as file:
                        #     print(f"GO: {index} -> {length - 1} by {sign}", file=file)
                        #     print(f"> {go_item}", file=file)
                index += 1

            return clan, go_rules

        return _cal_clan(
            self._lr1_rules, self._lr1_sign_name, self._lr1_signs, _first, _follow
        )

    def _cal_lr1_table(self) -> dict:
        """
        求LR(1)分析表

        :return: LR(1)分析表（结构：{"action": action, "goto": goto}）
        """
        # 先构建ACTION表
        action: dict = {}  # ACTION表
        # action[(f_state, sign)] = (action_type, action_value)
        # action_type: "shift", "reduce", "accept"
        # action_value: shift: 移进到的状态；reduce: 规约的产生式；accept: None
        action[(0, self._lr1_end)] = ("accept", None)
        # 再构建GOTO表
        goto: dict = {}  # GOTO表
        # goto[(f_state, sign)] = t_state
        goto[(0, self._entry)] = 0

        for i in range(len(self._lr1_clan)):
            # 处理每一个规范族
            for item in self._lr1_clan[i]:
                # 先处理移进操作
                if item[2] < len(item[1]):
                    # 如果GO(I, x) = J，且 x 是终结符,且 [A -> α.xβ , a] ∈ I
                    # 枚举终结符
                    for sign in self._lr1_signs:
                        if sign in self._lr1_sign_name.keys():
                            continue

                        # 判断[A -> α.xβ , a] ∈ I
                        if (
                            item[1][item[2]] == sign
                            and (i, sign) in self._lr1_go.keys()
                        ):
                            action[(i, sign)] = ("shift", self._lr1_go[(i, sign)])
                # 再处理规约操作
                elif item[2] == len(item[1]):
                    # 如果[A -> α. , b] ∈ I
                    for sign in item[3]:
                        # 先判断accept
                        if i == 0 and sign == self._lr1_end:
                            action[(i, sign)] = ("accept", None)
                        # 再判断规约
                        action[(i, sign)] = ("reduce", item)
                        # print(f"reduce: {i}, {sign}, {item}")

            for sign in self._lr1_sign_name.keys():
                # 如果GO(I, A) = J，且 A 是非终结符
                if (i, sign) in self._lr1_go.keys():
                    goto[(i, sign)] = self._lr1_go[(i, sign)]

        return {"action": action, "goto": goto}

    @staticmethod
    def add_tab(string: str, tab: int = 4) -> str:
        """
        添加tab
        """
        # 划分行
        lines = string.split("\n")
        # 添加tab
        lines = [f"{' ' * tab}{line}" for line in lines]
        return "\n".join(lines)

    def parse(self, tokens: list[tuple]) -> dict:
        """
        LR(1)解析，使用LR(1)分析表解析tokens

        :param tokens: 词法分析结果 (token_type, token_value, line, column)
        :return: 解析结果（语法树，字典形式）
        """
        try:
            tokens.append((self._lr1_end, None, None, None))  # 添加结束符
            # 初始化栈
            state_stack = [0]  # 状态栈
            sign_stack = [self._lr1_end]  # 符号栈
            syntax_stack = []  # 语法树栈，保存节点字典

            index = 0  # tokens索引
            while True:
                state = state_stack[-1]
                token_type, token_value, line, column = tokens[index]

                # 获取ACTION表项
                action = self._lr1_table["action"].get((state, token_type))
                if not action:
                    raise Exception(
                        f"Syntax error at token {token_value} (type: {token_type}) at line {line}, column {column}"
                    )

                action_type, action_value = action
                if action_type == "shift":
                    # Shift 操作，读取下一个Token
                    state_stack.append(action_value)
                    sign_stack.append(token_type)
                    # 将Token包装成语法树的叶子节点，压入语法树栈
                    syntax_stack.append(
                        {
                            "type": token_type,
                            "value": token_value,
                            "line": line,
                            "column": column,
                        }
                    )
                    index += 1
                elif action_type == "reduce":
                    # Reduce 操作，根据产生式进行规约
                    rule = action_value
                    left, right = rule[0], rule[1]
                    child_nodes = []
                    for _ in right:
                        # 从语法树栈中弹出子节点
                        child = syntax_stack.pop()
                        child_nodes.insert(0, child)
                        state_stack.pop()
                        sign_stack.pop()
                    node_type = self._lr1_sign_name.get(left, left)
                    if node_type == "":
                        # 如果类型名称为空，将子节点直接添加回语法树栈
                        syntax_stack.extend(child_nodes)
                    else:
                        # 创建新的非终结符节点
                        node = {"type": node_type, "children": child_nodes}
                        syntax_stack.append(node)
                    if left == "ENTRY":
                        state_stack.append(0)
                        continue
                    goto_state = self._lr1_table["goto"][(state_stack[-1], left)]
                    state_stack.append(goto_state)
                    sign_stack.append(left)
                elif action_type == "accept":
                    # 接受状态，解析完成
                    if len(syntax_stack) == 1:
                        return syntax_stack[0]
                    else:
                        # 将剩余的节点作为根节点的子节点返回
                        return {"type": "ROOT", "children": syntax_stack}
                else:
                    raise Exception("Syntax error!")

            raise Exception("Unexpected end of input")
        except Exception as e:
            # 可选：打印部分语法树栈，帮助调试
            # for node in syntax_stack:
            #     print(node)
            raise e


def save_as_json(syntax_tree: dict, path: str) -> None:
    """
    将语法树保存为JSON文件

    :param syntax_tree: 语法树
    :param path: JSON文件路径
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(syntax_tree, file, indent=4, ensure_ascii=False)


def test_parser():
    """
    测试语法分析器
    """
    lexer_instance = lexer.Lexer()
    parser_instance = Parser()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 创建输出目录
    BASE_DIR = f"{BASE_DIR}/../exe"
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    # 解析第一个C程序

    path = f"{BASE_DIR}/../in/palindrome.c"
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    lexer_instance.tokenize(content, True)
    tokens = lexer_instance.tokenize_result()
    syntax_tree = parser_instance.parse(tokens)

    # 将语法树写入JSON文件
    save_as_json(syntax_tree, f"{BASE_DIR}/palindrome.json")

    # 解析第二个C程序
    path = f"{BASE_DIR}/../in/doubleBubbleSort.c"
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
    lexer_instance.tokenize(content, True)
    tokens = lexer_instance.tokenize_result()
    syntax_tree = parser_instance.parse(tokens)

    # 将语法树写入JSON文件
    save_as_json(syntax_tree, f"{BASE_DIR}/doubleBubbleSort.json")


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
        test_parser()
    else:
        if (
            not args.input
            or not os.path.exists(args.input)
            or not args.input.endswith(".c")
        ):
            print("Please input correct file path and output path")
            exit(1)
        lexer_instance = lexer.Lexer()
        parser_instance = Parser()
        with open(args.input, "r", encoding="utf-8") as file:
            content = file.read()
        lexer_instance.tokenize(content, True)
        tokens = lexer_instance.tokenize_result()
        syntax_tree = parser_instance.parse(tokens)

        if not args.output:
            args.output = args.input.replace(".c", ".json")
        
        save_as_json(syntax_tree, args.output)
