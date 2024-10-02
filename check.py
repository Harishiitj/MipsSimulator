import re
reg_addressMap = {
    "$t0" : '00111',
    "$t1" : '01000',
    "$at" : '00001'
}

reg_values = {
    "00001" : 0
}

label_mem = {
    "label" : 4194336
}

itr = 4194324

line = "main: beq $t0, 100, label"
if ':' in line:
    line = line.split(':',1)[1].strip()

tokens = re.split(r'[,\s]+', line)
opcode = "000000"
immediate=""
if re.match(r'-?\d+', tokens[2]):  # Check if second operand is a register
    rs = reg_addressMap[tokens[1]]  # First register ($t1)
    reg_values["00001"] = int(tokens[2])
    rt = reg_addressMap["$at"]  # Second register ($t2)
    immediate = format(int((label_mem[tokens[3]]-itr-4)/4),'016b')

print(opcode+rs+rt+immediate)