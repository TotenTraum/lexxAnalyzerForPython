import io
import re
import token
import tokenize
from collections import deque

#          0   |   1   |   2   |   3   |   4   |   5   |   6   |   7   |   8   |   9
mtx = [[(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (6, 1), (9, 1)],  # 0 is newline
       [(1, 0), (8, 1), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0)],  # 1 is string
       [(0, 1), (1, 1), (2, 0), (3, 1), (4, 1), (9, 1), (9, 1), (7, 1), (8, 1), (9, 1)],  # 2 is number
       [(0, 1), (1, 1), (3, 0), (3, 0), (4, 1), (9, 1), (9, 1), (7, 1), (8, 1), (9, 1)],  # 3 is name
       [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (9, 1), (9, 1), (7, 1), (8, 1), (9, 0)],  # 4 is op
       [(1, 0), (1, 1), (2, 1), (3, 1), (4, 1), (5, 0), (9, 1), (7, 0), (5, 0), (9, 1)],  # 5 is indent  !5 6 7
       [(1, 0), (1, 1), (2, 1), (3, 1), (4, 1), (5, 0), (6, 0), (7, 1), (6, 0), (9, 1)],  # 6 is dedent  !5 6 7
       [(0, 1), (7, 0), (7, 0), (7, 0), (7, 0), (9, 1), (9, 1), (7, 0), (7, 0), (7, 0)],  # 7 is comment
       [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0)],  # 8 is divider
       [(0, 1), (9, 0), (9, 0), (9, 0), (9, 0), (9, 0), (9, 0), (7, 1), (8, 1), (9, 0)],  # 9 is nope ! 1 2 3 4 7 8
       ]

equ_id = {
    'newline': 0,
    'string': 1,
    'number': 2,
    'name': 3,
    'op': 4,
    'indent': 5,
    'dedent': 6,
    'comment': 7,
    'divider': 8,
    'nope': 9
}

equ_name = {
    0: 'newline',
    1: 'string',
    2: 'number',
    3: 'name',
    4: 'op',
    5: 'indent',
    6: 'dedent',
    7: 'comment',
    8: 'divider',
    9: 'nope'
}


# Сопоставляет символ с типом


def type_of(ch):
    match_number = re.fullmatch(r'\d', ch)
    match_char = re.fullmatch(r'\w', ch)
    match_whitespace = re.fullmatch(r' ', ch)
    match_operator = re.fullmatch(r'[\[\]{}()+\-\\*/=&%|:,.;><!_]', ch)
    match_string = re.fullmatch(r'[\'\"]', ch)
    match_nl = re.fullmatch(r'\n', ch)
    match_comment = re.fullmatch(r'#', ch)
    if match_number:
        return 'number'
    elif match_char:
        return 'name'
    elif match_operator:
        return 'op'
    elif match_whitespace:
        return 'divider'
    elif match_string:
        return 'string'
    elif match_nl:
        return 'newline'
    elif match_comment:
        return 'comment'
    else:
        return 'nope'


def type_to_state(cur_state, symbol_type):
    if cur_state == equ_id['newline'] and symbol_type == 'divider':
        return equ_id['dedent']
    else:
        return equ_id[symbol_type]


def is_double_op(first_char, second_char):
    if second_char == '=':
        return first_char == '=' or first_char == '<' or first_char == '>' or first_char == '!'
    if second_char == '*' and first_char == '*':
        return second_char == '*' and first_char == '*'
    if second_char == '\\' and first_char == '\\':
        return second_char == '\\' and first_char == '\\'
    return 0 == 1


def next_state(cur_state, str, i, level_stack: deque, op_stack: deque,
               prev_str_symbol: deque, str_symbol_stack: deque, dedent):
    ch = str[i]
    symbol_type = type_of(ch)
    state = type_to_state(cur_state, symbol_type)
    if state == equ_id['newline']:
        level_stack.appendleft(0)

    if cur_state == equ_id['indent'] or cur_state == equ_id['dedent']:
        cur_level = level_stack[0]
        prev_level = level_stack[1]
        if symbol_type == 'divider':
            cur_level += 1
            if cur_level >= prev_level and state == equ_id['divider']:
                state = equ_id['indent']
            level_stack[0] = cur_level

    if cur_state == equ_id['string'] and state == equ_id['string']:
        if len(op_stack) > 0:
            op = op_stack.pop()
            if op == '\\':
                state = equ_id['name']
            else:
                op_stack.clear()


    if state == equ_id['string']:
        if cur_state == equ_id['string']:
            if len(prev_str_symbol) > 0:
                if prev_str_symbol[0] != ch:
                    state = equ_id['name']
                else:
                    if len(str_symbol_stack) == 1 and str_symbol_stack[0] == ch:
                        if len(str) >= i + 1 and ch == str[i+1]:
                            state = equ_id['name']

                    str_symbol_stack.append(ch)

        else:
            prev_str_symbol.clear()
            prev_str_symbol.append(ch)
            str_symbol_stack.append(ch)
    else:
        str_symbol_stack.clear()


    # double op check
    if cur_state == equ_id['op'] and state == equ_id['op']:
        if len(op_stack) == 1:
            if is_double_op(op_stack[0], ch):
                if len(str) >= i + 1:
                    nxt_state = type_to_state(state, type_of(str[i + 1]))
                    i += 1
                    state = nxt_state
                    op_stack.clear()
        else:
            state = equ_id['nope']
        op_stack.clear()

    # push to op_stack if state == op, else clear op_stack
    if state == equ_id['op']:
        op_stack.append(ch)
    else:
        op_stack.clear()

    if cur_state == equ_id['newline'] and state != equ_id['dedent'] and level_stack[1] > 0:
        dedent = 1
    return i, state, dedent


def format_string(result: list, cur_state, index, last_pos, string: str, dedent):
    if cur_state == equ_id['string']:
        index += 1
    print_string = string[last_pos:index]
    if not (cur_state == equ_id['indent'] or cur_state == equ_id['dedent']):
        print_string = print_string.strip()
    if cur_state == equ_id['newline']:
        result.append("(%5i, %5i) %10s  |  %10s" % (last_pos, index, equ_name[cur_state], 'newline'))
        if dedent == 1:
            result.append("(%5i, %5i) %10s  |  %10s" % (last_pos, index, 'dedent', "''"))
            dedent = 0
    else:
        result.append("(%5i, %5i) %10s  |  %10s" % (last_pos, index, equ_name[cur_state], "'"+print_string+"'"))
    last_pos = index
    return index, last_pos, dedent


def analyze(string: str):
    string += ' '
    prev_str_symbols = deque([])
    str_symbols_stack = deque([])
    result = []
    level_stack = deque([0, 0])
    sym_stack = deque([])
    last_pos = 0
    dedent = 0
    cur_state = 8  # start from divider
    print(len(string))
    for i in range(0, len(string)):
        i, nxt_state, dedent = next_state(cur_state, string, i, level_stack, sym_stack,
                                          prev_str_symbols , str_symbols_stack, dedent)
        (to_state, end_state) = mtx[cur_state][nxt_state]
        if end_state == 1:
            i, last_pos, dedent = format_string(result, cur_state, i, last_pos, string, dedent)
        cur_state = to_state
    return result


prog_example = io.open("main.py").read()


def format_input_lang(string: str):
    return string.strip().replace('\t', '    ')

var = analyze(format_input_lang(prog_example))
for a in var:
    print(a)
