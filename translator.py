import sys
import json
import parser

address_data_mem = 0x0
address_instr_mem = 0x0
address2var = []
address2method = []
math_variables = ['+', '-', '/', '%', '*']
if_variables = ['>', '<', '>=', '<=', '!=', '=']
variables = set()
variables_method = set()
res_code = []
jmp_stack = []
reg_counter = 3
history = []


def translate(filename):
    global address_instr_mem, history

    with open(filename, encoding="utf-8") as file:
        text_code = file.read()

    s_expressions = parser.read(text_code)
    for se in s_expressions:
        check_args(se)

    history_defun = [item for item in history if item[0] == 'defun']
    history_other = [item for item in history if item[0] != 'defun']
    history = history_defun + history_other

    for i in range(0, len(history)):
        match history[i][0]:
            case "setq":
                parse_setq(history[i])
            case "if":
                parse_if(history[i])
            case "defun":
                for k in range(1, len(history[i][1]) - 1):
                    replacer(history[i][1], history[i][1][k], history[i][1][0])
                parse_def(history[i])
            case "loop":
                parse_loop(history[i])
            case "print":
                var_out(history[i][1])
            case "while":
                parse_while(history[i])

    res_code.append({'opcode': 'halt'})
    address_instr_mem += 1
    return res_code


def parse_while(el):
    global address_instr_mem
    start_addr_while = address_instr_mem
    operation_jmp = el[1].pop(-1)
    body = el[1]
    add_load_instr('rx15', 0)

    result = {
        'opcode': 0,
        'arg1': 0,
        'arg2': 0
    }

    add_load_instr('rx' + str(reg_counter), operation_jmp[1][1])
    change_data_reg()
    result.update({'arg2': 'rx' + str(get_prev_data_reg())})

    addr = get_var_addr_in_mem(operation_jmp[1][0])
    add_load_instr('rx2', addr)
    add_load_instr('rx' + str(reg_counter), 'rx2')
    change_data_reg()
    result.update({'arg1': 'rx' + str(get_prev_data_reg())})


    match operation_jmp[0]:
        case '>':
            result.update({'opcode': 'jle'})

        case '<':
            result.update({'opcode': 'jge'})

        case '=':
            result.update({'opcode': 'jne'})

        case '!=':
            result.update({'opcode': 'je'})

        case '>=':
            result.update({'opcode': 'jg'})

        case '<=':
            result.update({'opcode': 'jl'})

    res_code.append(result)
    address_instr_mem += 1

    for i in range(len(body)-1, -1, -1):
        match body[i][0]:
            case 'setq':
                parse_setq(body[i])
            case 'if':
                parse_if(body[i])
            case 'print':
                var_out(body[i][1])

    add_load_instr('rx15', start_addr_while)
    add_jmp_instr()
    end_addr_while = address_instr_mem
    res_code[start_addr_while].update({'arg2': end_addr_while})


def var_out(var_name):
    global address_instr_mem
    for var in address2var:
        if var['name'] == var_name[0]:
            if var['type'] == 'string':
                add_load_instr('rx2', var['addr'])
                reg_data = 'rx' + str(reg_counter)
                first_point = address_instr_mem
                add_load_instr('rx15', address_instr_mem + 7)
                add_load_instr(reg_data, 'rx2')
                res_code.append({'opcode': 'je', 'arg1': reg_data, 'arg2': 'rx0'})
                address_instr_mem += 1
                change_data_reg()
                res_code.append({'opcode': 'print', 'arg1': reg_data, 'arg2': 1})
                address_instr_mem += 1
                res_code.append({'opcode': 'inc', 'arg1': 'rx2'})
                address_instr_mem += 1
                add_load_instr('rx15', first_point)
                res_code.append({'opcode': 'jmp'})
                address_instr_mem += 1
                change_data_reg()
                break
            else:
                add_load_instr('rx2', var['addr'])
                reg_data = 'rx' + str(reg_counter)
                change_data_reg()
                add_load_instr(reg_data, 'rx2')
                res_code.append({'opcode': 'print', 'arg1': reg_data, 'arg2': 0})
                address_instr_mem += 1

def alloc_var(name, type = 'string'):
    global address_data_mem
    variables.add(name)
    var = {
        'addr': address_data_mem,
        'name': name,
        'type': type
    }
    address2var.append(var)
    address_data_mem += 2

def check_args(arg):
    operator = arg.operator
    args = []
    for a in arg.args:
        args.append(take_arg(a))
    if operator == "if":
        args[2] = history[len(history) - 2]
        history.pop(len(history) - 2)
        args[1] = history[len(history) - 1]
        history.pop(len(history) - 1)
        args[0] = history[len(history) - 1]
        history.pop(len(history) - 1)
    elif operator == "setq" and args[1] is None:
        args[1] = history[len(history) - 1]
        history.pop(len(history) - 1)
    elif operator == "defun" and args[-1] is None:
        args[-1] = history[len(history) - 1]
        history.pop(len(history) - 1)
    elif operator == "loop":
        history.pop(len(history) - 1)
        history.pop(len(history) - 1)
        args[2] = history[len(history) - 1]
        history.pop(len(history) - 1)
        args[1] = history[len(history) - 1]
        history.pop(len(history) - 1)
        args[0] = history[len(history) - 1]
        history.pop(len(history) - 1)
    elif operator == "while":
        for i in range(0, len(args)):
            args[i] = history[len(history) - 1]
            history.pop(len(history) - 1)


    elif operator in if_variables:
        if args[0] == None:
            args[0] = history[len(history) - 1]
            history.pop(len(history) - 1)

        if args[1] == None:
            args[1] = history[len(history) - 1]
            history.pop(len(history) - 1)


    history.append([operator, args])

def take_arg(arg):
    if isinstance(arg, str):
        return arg
    if isinstance(arg, int):
        return arg
    if arg.operator:
        return check_args(arg)
    else:
        return arg


def get_var_addr_in_mem(name):
    for var in address2var:
        if var['name'] == name:
            return var['addr']

def add_load_instr(register, value):
    global address_instr_mem
    res_code.append({'opcode': 'ld', 'arg1': register, 'arg2': value})
    address_instr_mem += 1

def add_wr_instr(register):
    global address_instr_mem
    res_code.append({'opcode': 'wr', 'arg1': register})
    address_instr_mem += 1

def change_data_reg():
    global reg_counter
    reg_counter += 1
    if reg_counter > 11:
        reg_counter = 3


def get_prev_data_reg():
    if reg_counter == 3:
        return 11
    else:
        return reg_counter - 1

def parse_setq(el):
    global address_data_mem
    global address_instr_mem
    name = el[1][0]
    reg_name = "rx" + str(reg_counter)
    var = el[1][1]

    if isinstance(el[1][1], str):
        if var[0] == '\"' and var[len(var) - 1] == '\"':
            if var[0] == "\"\"":
                add_load_instr('rx' + str(reg_counter), 0)
                change_data_reg()
                alloc_var(name, 'string')
                addr = get_var_addr_in_mem(name)
                add_wr_instr('rx' + str(get_prev_data_reg()))

                add_load_instr()
                return
            var = var.strip().replace("\"", "")
            if var == "":
                add_load_instr(reg_name, "rx0")
            else:
                for ch in range(0, len(var)):
                    ch_in_ord = ord(var[ch])
                    add_load_instr('rx' + str(reg_counter), ch_in_ord)
                    change_data_reg()
                    alloc_var(name, 'string')
                    addr = get_var_addr_in_mem(name)
                    add_wr_instr('rx' + str(get_prev_data_reg()))
        elif el[1][1] in variables:
            if not el[1][0] in variables:
                alloc_var(name, 'string')
            addr = get_var_addr_in_mem(var)
            add_load_instr('rx2', addr)
            add_load_instr('rx' + str(reg_counter), 'rx2')
            change_data_reg()

            addr = get_var_addr_in_mem(name)
            add_load_instr('rx2', addr)
            add_wr_instr(get_prev_data_reg())

        add_load_instr('rx' + str(reg_counter), 0x0)
        change_data_reg()
        alloc_var(name, 'string')
        add_wr_instr('rx' + str(get_prev_data_reg()))
        return

    elif isinstance(el[1][1], int):
        if not el[1][0] in variables:
            alloc_var(name, 'int')
        addr = get_var_addr_in_mem(name)
        add_load_instr('rx2', addr)
        add_load_instr('rx' + str(reg_counter), var)
        change_data_reg()
        add_wr_instr('rx' + str(get_prev_data_reg()))

    elif isinstance(var, list):
        if var[0] == 'read':
            alloc_var(name, 'string')
            addr = get_var_addr_in_mem(name)
            add_load_instr('rx2', addr)
            parse_read()
            add_wr_instr('rx0')
        elif var[0] == 'if':
            parse_if(var)
        elif var[0] in math_variables:
            reg = parse_math_method(var)
            addr = get_var_addr_in_mem(name)
            add_load_instr('rx2', addr)
            add_wr_instr('rx' + str(reg))
            res_code.append({'opcode': 'inc', 'arg1': 'rx2'})
            address_instr_mem += 1
            add_wr_instr('rx0')

        elif var[0] in variables_method:
            start_addr_method = get_start_addr_method(var[0])
            args_method = get_args_method(var[0])
            end_addr_method = get_end_addr_method(var[0])
            res_code[end_addr_method].update({'arg1': 'rx' + str(address_instr_mem)})

            for arg_index in range(len(args_method)):
                addr = get_var_addr_in_mem(args_method[arg_index])
                add_load_instr('rx2', addr)
                add_load_instr('rx' + str(address_instr_mem), var[1][arg_index])
                change_data_reg()
                add_wr_instr('rx' + str(get_prev_data_reg()))

            add_load_instr('rx15', start_addr_method)
            add_jmp_instr()
            add_wr_instr('rx' + str(get_prev_data_reg()))


def get_start_addr_method(name):
    for method in address2method:
        if method['name'] == name:
            return method['start_addr']

def get_args_method(name):
    for method in address2method:
        if method['name'] == name:
            return method['args']

def get_end_addr_method(name):
    for method in address2method:
        if method['name'] == name:
            return method['end_addr']

def alloc_method(start_addr, name, args, end_addr):
    global address_instr_mem
    variables_method.add(name)
    method = {
        'start_addr': start_addr,
        'name': name,
        'args': args,
        'end_addr': end_addr
    }
    address2method.append(method)

def parse_loop(el):
    global address_instr_mem
    jmp_stack.append({'com_addr': address_instr_mem, 'type': 'loop'})

    if el[1][0][0] == "setq":
        parse_setq(el[1][0])
    elif el[1][0][0] in variables_method:
        start_addr_method = get_start_addr_method(el[1][0][0])
        args_method = get_args_method(el[1][0][0])
        end_addr_method = get_end_addr_method(el[1][0][0])
        res_code[end_addr_method].update(
            {'arg1': 'rx' + str(address_instr_mem)})

        for arg_index in range(len(args_method)):
            addr = get_var_addr_in_mem(args_method[arg_index])
            add_load_instr('rx2', addr)
            add_load_instr('rx' + str(address_instr_mem),
                           el[1][0][1][arg_index])
            change_data_reg()
            add_wr_instr('rx' + str(get_prev_data_reg()))

        add_load_instr('rx15', start_addr_method)
        add_jmp_instr()

    parse_setq(el[1][1])

    add_load_instr('rx15', jmp_stack.pop()["com_addr"])

    jmp_block={
        'opcode': 'jle',
        'arg1': 0,
        'arg2': 0
    }
    addr_var = get_var_addr_in_mem(el[1][2][1][0])
    add_load_instr('rx2', addr_var)
    add_load_instr('rx' + str(reg_counter), 'rx2')
    jmp_block.update({'arg1': 'rx' + str(reg_counter)})
    change_data_reg()
    add_load_instr('rx' + str(reg_counter), el[1][2][1][1])
    jmp_block.update({'arg2': 'rx' + str(reg_counter)})
    change_data_reg()

    res_code.append(jmp_block)


def add_jmp_instr():
    global address_instr_mem
    res_code.append({'opcode': 'jmp'})
    address_instr_mem += 1

def parse_def(el):
    global address_instr_mem
    method_args = []
    name = el[1][0]
    for i in range(1,len(el[1])-1):
        method_args.append(el[1][i])
    method_body = el[1][-1]
    for i in range(0, len(method_args)):
        alloc_var(method_args[i], 'int')

    jmp_instr_addr = address_instr_mem
    add_load_instr("rx15", 0)
    add_jmp_instr()

    start_instr_addr = address_instr_mem

    # for i in range(0, len(method_body)):
    #     match method_body[i][0]:
    #         case "setq":
    #             parse_setq(method_body[i])
    #         case "if":
    #             parse_if(method_body[i])
    #         case "loop":
    #             parse_loop(method_body[i])



    match method_body[0]:
        case "setq":
            parse_setq(method_body)
        case "if":
            parse_if(method_body)
        case "loop":
            parse_loop(method_body)

    if method_body[0] in math_variables:
        parse_math_method(method_body)

    end_instr_addr = address_instr_mem
    alloc_method(start_instr_addr, name, method_args, end_instr_addr)


    jmp_var = address_instr_mem + 2
    add_load_instr("rx15", jmp_var)
    add_jmp_instr()

    res_code[jmp_instr_addr].update({'arg2': address_instr_mem})


def check_number_in_arg(row):
    try:
        float(row)
        return True
    except ValueError:
        return False


def load_var(addr):
    add_load_instr('rx2', addr)
    add_load_instr('rx' + str(reg_counter), 'rx2')
    change_data_reg()
    return get_prev_data_reg()

def parse_math_method(el):
    global address_instr_mem

    result = {
        'opcode': 0,
        'arg1': 0,
        'arg2': 0
    }

    var_left = el[1][0]
    var_right = el[1][1]

    if isinstance(var_right, list):
        rx_var_right = parse_math_method(var_right)
    elif check_number_in_arg(var_right):
        add_load_instr('rx' + str(reg_counter), var_right)
        rx_var_right = reg_counter
        change_data_reg()
    elif var_right in variables:
        rx_var_right = load_var(get_var_addr_in_mem(var_right))
    else:
        rx_var_right = 0



    if isinstance(var_left, list):
        rx_var_left = parse_math_method(var_left)
    elif check_number_in_arg(var_left):
        add_load_instr('rx' + str(reg_counter), var_left)
        rx_var_left = reg_counter
        change_data_reg()
    elif var_left in variables:
        rx_var_left = load_var(get_var_addr_in_mem(var_left))
    else:
        rx_var_left = 0

    result.update({'arg1': 'rx' + str(rx_var_left), 'arg2':'rx'+ str(rx_var_right)})

    match el[0]:
        case '+':
            result.update({'opcode': 'add'})
        case '-':
            result.update({'opcode': 'sub'})
        case '/':
            result.update({'opcode': 'div'})
            rx_var_left = 13
        case '%':
            result.update({'opcode': 'div'})
            rx_var_left = 14
        case '*':
            result.update({'opcode': 'mul'})

    res_code.append(result)
    address_instr_mem += 1
    return rx_var_left


def parse_condition(args):
    global address_instr_mem
    result = {
        'opcode': 0,
        'arg1': 0,
        'arg2': 0
    }

    operation = args[0][0]
    left = args[0][1][0]
    right = args[0][1][1]

    if not isinstance(left, int) and len(left) > 1:
        if left[0] in variables_method:
            start_addr_method = get_start_addr_method(left[0])
            args_method = get_args_method(left[0])
            end_addr_method = get_end_addr_method(left[0])
            res_code[end_addr_method].update({'arg1': 'rx' + str(address_instr_mem)})

            for arg_index in range(len(args_method)):
                addr = get_var_addr_in_mem(args_method[arg_index])
                add_load_instr('rx2', addr)
                add_load_instr('rx' + str(address_instr_mem), left[1][arg_index])
                change_data_reg()
                add_wr_instr('rx' + str(get_prev_data_reg()))

            add_load_instr('rx15', start_addr_method)
            add_jmp_instr()

        elif left[0] in math_variables:
            reg = 'rx' + str(parse_math_method(left))
            result.update({'arg1': reg})

        elif left[0] == 'if':
            parse_if(left)
            result.update({'arg1': 'rx' + str(get_prev_data_reg())})

        elif left[0] == 'setq':
            parse_setq(left)
            result.update({'arg1': 'rx' + str(get_prev_data_reg())})
    else:
        if left in variables:
            reg = 'rx' + str(load_var(get_var_addr_in_mem(left)))
            result.update({'arg1': reg})
        elif left == '0':
            result.update({'arg1': 'rx0'})
        elif check_number_in_arg(left):
            add_load_instr("rx" + str(reg_counter), int(left))
            result.update({'arg1': "rx" + str(reg_counter)})
            change_data_reg()
        elif left[0] == 'EOF':
            result.update({'arg1': 'rx0'})


    if not isinstance(right, int) and len(right) > 1:
        if right[0] in variables_method:
            start_addr_method = get_start_addr_method(right[0])
            args_method = get_args_method(right[0])
            end_addr_method = get_end_addr_method(right[0])
            res_code[end_addr_method].update({'arg2': 'rx' + str(address_instr_mem)})

            for arg_index in range(len(args_method)):
                addr = get_var_addr_in_mem(args_method[arg_index])
                add_load_instr('rx2', addr)
                add_load_instr('rx' + str(address_instr_mem), left[1][arg_index])
                change_data_reg()
                add_wr_instr('rx' + str(get_prev_data_reg()))

            add_load_instr('rx15', start_addr_method)
            add_jmp_instr()

        elif right[0] in math_variables:
            reg = 'rx' + str(parse_math_method(right))
            result.update({'arg2': reg})

        elif right[0] == 'if':
            parse_if(left)
            result.update({'arg2': 'rx' + str(get_prev_data_reg())})

        elif right[0] == 'setq':
            parse_setq(left)
            result.update({'arg2': 'rx' + str(get_prev_data_reg())})

    else:
        if right in variables:
            reg = 'rx' + str(load_var(get_var_addr_in_mem(right[0])))
            result.update({'arg2': reg})
        elif right == '0':
            result.update({'arg2': 'rx0'})
        elif check_number_in_arg(right):
            add_load_instr("rx" + str(reg_counter), int(right))
            result.update({'arg2': "rx" + str(reg_counter)})
            change_data_reg()
        elif right[0] == 'EOF':
            result.update({'arg2': 'rx0'})

    match operation:
        case '>':
            result.update({'opcode': 'jle'})

        case '<':
            result.update({'opcode': 'jge'})

        case '=':
            result.update({'opcode': 'jne'})

        case '!=':
            result.update({'opcode': 'je'})

        case '>=':
            result.update({'opcode': 'jl'})

        case '<=':
            result.update({'opcode': 'jg'})

    true_jmp_addr = address_instr_mem
    add_load_instr('rx15', address_instr_mem)

    res_code.append(result)
    address_instr_mem += 1
    if isinstance(args[1], int):
        add_load_instr('rx' + str(reg_counter), args[1])
    elif args[1][0] == 'setq':
        if isinstance(args[1][1][1], int):
            addr = get_var_addr_in_mem(args[1][1][0])
            add_load_instr('rx2', addr)
            add_load_instr('rx' + str(reg_counter), args[1][1][1])
            add_wr_instr('rx' + str(reg_counter))
            change_data_reg()
        else:
            reg = parse_math_method(args[1][1][1])
            addr = get_var_addr_in_mem(args[1][1][0])
            add_load_instr('rx2', addr)
            add_wr_instr('rx' + str(reg))
    elif args[1][0] == 'print':
        var_out(args[1][1][0])

    false_jmp_addr = address_instr_mem
    add_load_instr('rx15', address_instr_mem)
    add_jmp_instr()

    res_code[true_jmp_addr].update({'arg2': address_instr_mem})
    if isinstance(args[2], int):
        add_load_instr('rx' + str(reg_counter), args[2])
    elif args[2][0] == 'setq':
        if isinstance(args[2][1][1], int):
            addr = get_var_addr_in_mem(args[2][1][0])
            add_load_instr('rx2', addr)
            add_load_instr('rx' + str(reg_counter), args[2][1][1])
            add_wr_instr('rx' + str(reg_counter))
            change_data_reg()
        else:
            reg = parse_math_method(args[2][1][1])
            addr = get_var_addr_in_mem(args[2][1][0])
            add_load_instr('rx2', addr)
            add_wr_instr('rx' + str(reg))
    elif args[2][0] == 'print':
        var_out(args[2][1][0])

    change_data_reg()
    res_code[false_jmp_addr].update({'arg2': address_instr_mem})

def parse_read():
    global address_instr_mem
    res_code.append({'opcode': 'input'})
    address_instr_mem += 1
    add_load_instr('rx15', address_instr_mem - 1)
    res_code.append({'opcode': 'dec', 'arg1': 'rx2'})
    address_instr_mem += 1
    for_check_reg = 'rx' + str(reg_counter)
    add_load_instr(for_check_reg, 'rx2')
    change_data_reg()
    res_code.append({'opcode': 'inc', 'arg1': 'rx2'})
    address_instr_mem += 1
    add_load_instr('rx' + str(reg_counter), ord('"'))
    change_data_reg()
    res_code.append({'opcode': 'jne', 'arg1': for_check_reg, 'arg2': 'rx' + str(get_prev_data_reg())})
    address_instr_mem += 1
    res_code.append({'opcode': 'dec', 'arg1': 'rx2'})
    address_instr_mem += 1
    add_load_instr('rx' + str(reg_counter), 0x0)
    change_data_reg()
    add_wr_instr('rx' + str(get_prev_data_reg()))


def parse_if(el):
    global address_instr_mem
    jmp_instr_addr = address_instr_mem
    add_load_instr("rx15", 0)
    parse_condition(el[1])
    res_code[jmp_instr_addr].update({'arg2': address_instr_mem})


def replacer(array_of_arrays, parameter, fun_name):
    for i, sub_array in enumerate(array_of_arrays):
        if isinstance(sub_array, list):
            replacer(sub_array, parameter, fun_name)
        else:
            if sub_array == parameter:
                array_of_arrays[i] = fun_name + '_' + parameter + '_var'


def write_code(filename, code):
    with open(filename, "w", encoding='utf-8') as file:

        file.write(json.dumps(code, indent=4))


def main(args):
    assert len(args) == 2, "Wrong arguments"
    source, target = args
    opcodes = translate(source)
    write_code(target, opcodes)


if __name__ == '__main__':
    main(sys.argv[1:])
