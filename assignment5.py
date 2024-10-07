import re

# region definations
# register address map
reg_addressMap = {
    '$zero': '00000', '$0': '00000',
    '$at': '00001', '$1': '00001',
    '$v0': '00010', '$2': '00010',
    '$v1': '00011', '$3': '00011',
    '$a0': '00100', '$4': '00100',
    '$a1': '00101', '$5': '00101',
    '$a2': '00110', '$6': '00110',
    '$a3': '00111', '$7': '00111',
    '$t0': '01000', '$8': '01000',
    '$t1': '01001', '$9': '01001',
    '$t2': '01010', '$10': '01010',
    '$t3': '01011', '$11': '01011',
    '$t4': '01100', '$12': '01100',
    '$t5': '01101', '$13': '01101',
    '$t6': '01110', '$14': '01110',
    '$t7': '01111', '$15': '01111',
    '$s0': '10000', '$16': '10000',
    '$s1': '10001', '$17': '10001',
    '$s2': '10010', '$18': '10010',
    '$s3': '10011', '$19': '10011',
    '$s4': '10100', '$20': '10100',
    '$s5': '10101', '$21': '10101',
    '$s6': '10110', '$22': '10110',
    '$s7': '10111', '$23': '10111',
    '$t8': '11000', '$24': '11000',
    '$t9': '11001', '$25': '11001',
    '$k0': '11010', '$26': '11010',
    '$k1': '11011', '$27': '11011',
    '$gp': '11100', '$28': '11100',
    '$sp': '11101', '$29': '11101',
    '$fp': '11110', '$30': '11110',
    '$ra': '11111', '$31': '11111'
}

# register values
reg_values = {
    '00000': 0,
    '00001': 0,
    '00010': 0,
    '00011': 0,
    '00100': 0,
    '00101': 0,
    '00110': 0,
    '00111': 0,
    '01000': 0,
    '01001': 0,
    '01010': 0,
    '01011': 0,
    '01100': 0,
    '01101': 0,
    '01110': 0,
    '01111': 0,
    '10000': 0,
    '10001': 0,
    '10010': 0,
    '10011': 0,
    '10100': 0,
    '10101': 0,
    '10110': 0,
    '10111': 0,
    '11000': 0,
    '11001': 0,
    '11010': 0,
    '11011': 0,
    '11100': 0,
    '11101': 0,
    '11110': 0,
    '11111': 0
}


# define data memory
mem_start_address = 268500992
filled = 0
data_memory = {}

# define label mem
label_mem = {}

# define program counter
pc_start = 4194304
pc = pc_start

# define instruction memory
instruction_memory = ""

branching_queue = []

# instrunction type
instruction_type = {
    # R-type instructions
    'add': 'R-type',
    'sub': 'R-type',
    'and': 'R-type',
    'or': 'R-type',
    'slt': 'R-type',

    # I-type instructions
    'lui': 'I-type',
    'ori': 'I-type',
    'addi': 'I-type',    # Add immediate
    'lw': 'I-type',      # Load word
    'beq': 'I-type',     # Branch if equal

    # J-type instructions
    'j': 'J-type',       # Jump
}

# instruction Opcode mapping
opcode_dict = {
    # I-type instructions
    'lui': '001111',
    'ori': '001101',
    'addi': '001000',   # Add immediate
    'lw': '100011',     # Load word
    'beq': '000100',    # Branch if equal
    'addiu': '001001',
    # J-type instructions
    'j': '000010',      # Jump
}

# instruction func bits mapping
funct_dict = {
    'add': '100000',    # Addition
    'sub': '100010',    # Subtraction
    'and': '100100',    # Bitwise AND
    'or': '100101',     # Bitwise OR
    'slt': '101010',    # Set less than
}

# endregion

# parse .data section


def parse_data_section(lines):
    global filled
    current_label = None
    for line in lines:
        # Remove comments and extra spaces
        line = re.sub(r'#.*', '', line).strip()

        if not line:
            continue

        # Check for labels
        if ':' in line:
            parts = line.split(':')
            current_label = parts[0].strip()  # Label before ':'
            line = parts[1].strip() if len(parts) > 1 else None

        if current_label:
            # Handle different data types (with only one value per label)
            if '.word' in line:
                # Store a single word (4 bytes) in memory
                value = int(line.split('.word')[1].strip())
                if filled % 4 != 0:
                    filled += 4 - (filled % 4)
                label_mem[current_label] = mem_start_address+filled
                data_memory[mem_start_address+filled] = value
                filled += 4
                current_label = None

            elif '.float' in line:
                # Store a single floating-point value
                value = float(line.split('.float')[1].strip())
                if filled % 4 != 0:
                    filled += 4 - filled % 4
                label_mem[current_label] = mem_start_address+filled
                data_memory[mem_start_address+filled] = value
                filled += 4
                current_label = None

            elif '.asciiz' in line:
                # Store a single null-terminated ASCII string
                string = line.split('.asciiz')[1].strip().strip('"')
                label_mem[current_label] = mem_start_address+filled
                data_memory[mem_start_address + filled] = string + '\0'
                filled += len(string)+1
                current_label = None

            elif '.space' in line:
                # Reserve space (specified number of bytes)
                size = int(line.split('.space')[1].strip())
                label_mem[current_label] = mem_start_address + \
                    filled  # Reserve with '0' as placeholders
                data_memory[mem_start_address + filled] = '\0' * size
                filled += size
                current_label = None

# Parse .text section


def parse_text_section(lines):
    global instruction_memory
    text_section = True
    itr = pc_start
    for line in lines:
        # Remove inline comments and strip extra spaces
        line = re.sub(r'#.*', '', line).strip()

        if ':' in line:
            # Remove everything before and including the first colon
            subroutine_label = line.split(':')[0].strip()
            label_mem[subroutine_label] = itr
            line = line.split(':', 1)[1].strip()

        if not line:
            continue

        elif text_section:
            tokens = re.split(r'[,\s]+', line)
            tokens = [token for token in tokens if token]
            instruction = tokens[0]
            if instruction in opcode_dict:  # I-type or J-type instruction
                if (instruction == "lw"):
                    itr = ins_lw(tokens, itr)

                elif (instruction == "beq"):
                    itr = ins_beq(tokens, itr)

                elif (instruction == "j"):
                    itr = ins_jump(tokens, itr)

                elif (instruction == "addi"):
                    itr = ins_addi(tokens, itr)

            # R-type instruction(Completed) (Only 1 instruction template for each R-type instruction)
            elif instruction in funct_dict:
                itr = ins_rtype(tokens, itr)

            elif (instruction == "la"):  # Handle the 'la' instruction
                # la $t0, label
                rt = tokens[1]
                address = tokens[2]
                itr = ins_la(rt, address, itr)

            elif instruction == "li":  # li $t0,100
                rt = tokens[1]
                immediate = tokens[2]
                itr = ins_li(tokens, itr)

    instruction_memory = update_instructions()
    return instruction_memory


def ins_lw(tokens, itr):
    global instruction_memory
    opcode = opcode_dict[tokens[0]]
    immediate = ""
    rs = ""
    rt = reg_addressMap[tokens[1]]
    # case: lw $t1, -100($t0)
    if re.match(r'[-]?\d+\(\$\w+\)', tokens[2]):
        match = re.match(r'([-]?\d+)\((\$\w+)\)', tokens[2])
        immediate = bin(int(match.group(1)) & 0xFFFF)[
            2:].zfill(16)  # Immediate value
        rs = reg_addressMap[match.group(2)]  # Base register
        instruction_memory += opcode+rs+rt+immediate
        itr += 4

    # Case: lw $t1, ($t2)
    elif re.match(r'\(\$\w+\)', tokens[2]):
        immediate = "0000000000000000"  # Zero offset
        rs = reg_addressMap[re.match(
            r'\(\$(\w+)\)', tokens[2]).group(1)]  # Base register
        instruction_memory += opcode+rs+rt+immediate
        itr += 4

    # Case: lw $t1, label
    elif tokens[2] in label_mem:
        # Label address as immediate
        lui_imm_binary = format(mem_start_address, '032b')
        itr = ins_lui(rt="$at", immediate=lui_imm_binary[:16], itr=itr)
        immediate = label_mem[tokens[2]] - mem_start_address
        t3 = str(immediate)+'('+"$at"+')'
        tokens1 = ["lw", tokens[1], t3]
        itr = ins_lw(tokens=tokens1, itr=itr)
    return itr


def ins_beq(tokens, itr):
    global instruction_memory
    opcode = opcode_dict[tokens[0]]
    immediate = ""
    # Handle the case of beq $t1, $t2, label (Register-Register)
    # Check if second operand is a register
    if re.match(r'\$\w+', tokens[2]):
        rs = reg_addressMap[tokens[1]]  # First register ($t1)
        rt = reg_addressMap[tokens[2]]  # Second register ($t2)
        label = tokens[3]               # The label
        # immediate = format(int((label_mem[label]-itr-4)/4),'016b')
        immediate = "0000000000000000"
        branching_queue.append(("beq", itr, tokens[3]))
        instruction_memory += opcode + rs + rt + immediate
        itr += 4

    # Handle the case of beq $t1, immediate, label (Register-Immediate)
    # Check if second operand is an immediate
    elif re.match(r'-?\d+', tokens[2]):
        tokens1 = ["addi", "$at", "$zero", tokens[2]]
        itr = ins_addi(tokens1, itr)
        label = tokens[3]
        tokens1 = ["beq", "$at", tokens[1], label]
        itr = ins_beq(tokens1, itr)
    return itr


def ins_jump(tokens, itr):
    global instruction_memory
    # j loop1
    label = tokens[1]  # the label to jump to
    # convert the target address to a 26-bit binary value with 2 right shift
    # address = format(int(label_mem[label] / 4), '026b')
    address = "00000000000000000000000000"
    branching_queue.append(("jump", itr, label))
    instruction_memory += opcode_dict[tokens[0]]+address
    itr += 4
    return itr


def ins_lui(rt, immediate, itr):  # immediate should be in binary string format rs = "$t0" or "$8" form
    global instruction_memory
    rt_add = reg_addressMap[rt]
    instruction_memory += '001111'+'00000'+rt_add+immediate
    itr += 4
    return itr


# immediate should be in binary string format rs/rt = "$t0" or "$8" form
def ins_ori(rs, rt, immediate, itr):
    global instruction_memory
    rt_add = reg_addressMap[rt]
    rs_add = reg_addressMap[rs]
    instruction_memory += '001101'+rs_add+rt_add+immediate
    itr += 4
    return itr


def ins_addi(tokens, itr):
    global instruction_memory
    # Extract components from the tokens
    opcode = opcode_dict[tokens[0]]  # opcode for addi is in opcode_dict
    rt = reg_addressMap[tokens[1]]  # Destination register ($t1)
    rs = reg_addressMap[tokens[2]]  # Source register ($t2)

    # Parse the immediate value (tokens[3])
    immediate_value = int(tokens[3])

    # Check if the immediate fits in 16 bits (signed)
    if -32768 <= immediate_value <= 32767:
        # Handle the case of a 16-bit signed immediate
        # Convert to 16-bit binary, masking the value
        imm_binary = format(immediate_value & 0xFFFF, '016b')
        # Use last 16 bits if it's larger than 16-bit
        instruction_memory += opcode + rs + rt + imm_binary
        itr += 4

    else:
        # Handle the case of a 32-bit immediate (assuming extended support)
        imm_binary = format(immediate_value & 0xFFFFFFFF,
                            '032b')  # Convert to 32-bit binary
        itr = ins_lui(rt="$at", immediate=imm_binary[:16], itr=itr)
        itr = ins_ori(rs="$at", rt="$at", immediate=imm_binary[15:], itr=itr)
        tokens1 = ["add", tokens[1], tokens[2], "$at"]
        itr = ins_rtype(tokens1, itr=itr)
    return itr


def ins_addiu(tokens, itr):
    global instruction_memory
    # Extract components from the tokens
    opcode = opcode_dict["addiu"]  # opcode for addiu
    rt = reg_addressMap[tokens[1]]  # Destination register ($t1)
    rs = reg_addressMap[tokens[2]]  # Source register ($t2)

    # Parse the immediate value (tokens[3])
    immediate_value = int(tokens[3])

    # Check if the immediate fits in 16 bits (unsigned)
    if 0 <= immediate_value <= 65535:
        # Handle the case of a 16-bit unsigned immediate
        imm_binary = format(immediate_value & 0xFFFF, '016b')
        # Add the instruction to the instruction memory
        instruction_memory += opcode + rs + rt + imm_binary
        itr += 4

    else:
        # For 32-bit immediate values, split it with lui and ori
        imm_binary = format(immediate_value & 0xFFFFFFFF, '032b')
        # Use lui and ori to load the 32-bit immediate into $at
        itr = ins_lui(rt="$at", immediate=imm_binary[:16], itr=itr)
        itr = ins_ori(rs="$at", rt="$at", immediate=imm_binary[16:], itr=itr)
        # Then use add to add the base register
        tokens1 = ["add", tokens[1], tokens[2], "$at"]
        itr = ins_rtype(tokens1, itr=itr)

    return itr


def ins_la(rt, address, itr):
    global instruction_memory
    if address in label_mem:
        # Get the actual address from the label
        address = label_mem[address]

    immediate_value = int(address)
    if 0 <= immediate_value <= 65535:
        # Use addi instruction for 16-bit immediate
        immediate_bin = format(immediate_value, '016b')
        itr = ins_ori("$zero", rt, immediate_bin, itr)

    elif -32768 <= immediate_value < 0:
        # Use addi instruction for 16-bit immediate
        tokens = ["addiu", rt, "$zero", str(immediate_value)]
        itr = ins_addi(tokens, itr)

    else:
        # Handle 32-bit immediate using lui and ori
        immediate_binary = format(immediate_value & 0xFFFFFFFF, '032b')
        itr = ins_lui(rt="$at", immediate=immediate_binary[:16], itr=itr)
        itr = ins_ori(rs="$at", rt=rt,
                      immediate=immediate_binary[16:], itr=itr)

    return itr


def ins_li(tokens, itr):
    global instruction_memory
    rt = reg_addressMap[tokens[1]]  # Destination register (e.g., $t1)
    immediate_value = int(tokens[2])  # Immediate value (e.g., 100 or -100)

    # Case 1: 16-bit signed immediate (sign-extended)
    if -32768 <= immediate_value <= 32767:
        # Use addiu for small immediate values (sign-extended)
        imm_binary = format(immediate_value & 0xFFFF, '016b')
        instruction_memory += '001001' + '00000' + rt + \
            imm_binary  # 'addiu $t1, $zero, immediate'
        itr += 4

    # Case 2: 16-bit unsigned immediate (zero-extended)
    elif 0 <= immediate_value <= 65535:
        # Handle 16-bit unsigned immediate (zero-extended)
        imm_binary = format(immediate_value & 0xFFFF, '016b')
        # tokens = ["ori", "$zero", tokens[1], imm_binary]
        itr = ins_ori("$zero", tokens[1], imm_binary, itr)

    # Case 3: 32-bit immediate (handled using LUI and ORI)
    else:
        imm_binary = format(immediate_value & 0xFFFFFFFF,
                            '032b')  # Convert to 32-bit binary
        # Load upper 16 bits with LUI
        itr = ins_lui(rt="$at", immediate=imm_binary[:16], itr=itr)
        # Load lower 16 bits with ORI
        itr = ins_ori(rs="$at", rt=tokens[1],
                      immediate=imm_binary[16:], itr=itr)

    return itr


def ins_rtype(tokens, itr):
    global instruction_memory
    # R-type instruction(Completed) (Only 1 instruction template for each R-type instruction)
    opcode = '000000'
    instruction = tokens[0]
    rs = reg_addressMap[tokens[2]]
    rt = reg_addressMap[tokens[3]]
    rd = reg_addressMap[tokens[1]]
    func = funct_dict[instruction]
    instruction_memory += opcode + rs + rt + rd + '00000' + func
    itr += 4
    return itr

# necessary during execution


def signExtend(bin_string):
    # Check the most significant bit (MSB)
    msb = bin_string[0]
    # Extend with 16 copies of the MSB
    sign_extended = msb * 16 + bin_string
    return sign_extended


def signedBinToInt32(bin_string):
    # Convert binary string to integer
    integer_value = int(bin_string, 2)

    # Check if the binary string represents a negative number
    if bin_string[0] == '1':  # If the sign bit is set
        # Perform two's complement to get the negative value
        integer_value -= 2**32  # Subtract 2^32 for signed interpretation
    return integer_value


def signedBinToInt16(bin_string):
    # Convert binary string to integer
    integer_value = int(bin_string, 2)

    # Check if the binary string represents a negative number
    if bin_string[0] == '1':  # If the sign bit is set
        # Perform two's complement to get the negative value
        integer_value -= 2**16  # Subtract 2^32 for signed interpretation
    return integer_value

# updateinstructions for branching instructions


def update_instructions():
    global instruction_memory
    instruction_list = list(instruction_memory)
    while (len(branching_queue) > 0):
        instruction = branching_queue.pop()   # type ("beq", itr, label)
        instruction_address = 8*(instruction[1]-pc_start)
        if (instruction[0] == "beq"):
            imm_binary = format(
                int((label_mem[instruction[2]]-instruction[1]-4)/4) & 0xFFFF, '016b')
            instruction_list[instruction_address +
                             16:instruction_address+32] = imm_binary
        elif (instruction[0] == "jump"):
            imm_binary = format(int(label_mem[instruction[2]] / 4), '026b')
            instruction_list[instruction_address +
                             6:instruction_address+32] = imm_binary
    instruction_memory = "".join(instruction_list)
    return instruction_memory

# Function to parse a .asm file


def parse_asm_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        in_data_section = False
        in_text_section = False
        data_section_lines = []
        text_section_lines = []

        # Split .data and .text sections
        for line in lines:
            if '.data' in line:
                in_data_section = True
                in_text_section = False
            elif '.text' in line:
                in_text_section = True
                in_data_section = False
            elif in_data_section:
                data_section_lines.append(line)
            elif in_text_section:
                text_section_lines.append(line)

        # Parse .data sections
        parse_data_section(data_section_lines)

        # Parse .text section
        parse_text_section(text_section_lines)

# Instruction Decoding


def decode_and_execute(instruction, curr_pc):
    # All Mips Datapath value
    opcode = instruction[0:6]  # First 6 bits are the opcode
    rs = instruction[6:11]
    rt = instruction[11:16]
    rd = instruction[16:21]
    # shift amount (not used in your current instructions)
    shamt = instruction[21:26]
    funct = instruction[26:32]  # Last 6 bits are the function code
    immediate = instruction[16:32]
    sign_extend = immediate
    if immediate[0] == '0':
        sign_extend = '0000000000000000' + sign_extend
    else:
        sign_extend = '1111111111111111' + sign_extend
    address = instruction[6:32]
    next_pc = format((curr_pc + 4) & 0xFFFFFFFF, '032b')
    jump_add = next_pc[0:4] + address + '00'
    branch_add = format(
        (int(next_pc, 2) + (int(sign_extend, 2) << 2)) & 0xFFFFFFFF, '032b')

    control_signals = {
        "RegDst": None,
        "Jump": None,
        "Branch": None,
        "MemRead": None,
        "MemtoReg": None,
        "ALUOp": None,
        "MemWrite": None,
        "ALUSrc": None,
        "RegWrite": None
    }

    # Decoding the instruction based on opcode
    if opcode == '000000':  # R-type instruction
        control_signals["RegDst"] = 1
        control_signals["ALUSrc"] = 0
        control_signals["MemtoReg"] = 0
        control_signals["RegWrite"] = 1
        control_signals["MemRead"] = 0
        control_signals["MemWrite"] = 0
        control_signals["Branch"] = 0
        control_signals["Jump"] = 0
        control_signals["ALUOp"] = '10'  # ALU operation depends on funct field

    elif opcode == '100011':  # lw instruction
        control_signals["RegDst"] = 0
        control_signals["ALUSrc"] = 1
        control_signals["MemtoReg"] = 1
        control_signals["RegWrite"] = 1
        control_signals["MemRead"] = 1
        control_signals["MemWrite"] = 0
        control_signals["Branch"] = 0
        control_signals["Jump"] = 0
        control_signals["ALUOp"] = '00'  # ALU performs addition

    elif opcode == '101011':  # sw instruction
        control_signals["RegDst"] = None
        control_signals["ALUSrc"] = 1
        control_signals["MemtoReg"] = None
        control_signals["RegWrite"] = 0
        control_signals["MemRead"] = 0
        control_signals["MemWrite"] = 1
        control_signals["Branch"] = 0
        control_signals["Jump"] = 0
        control_signals["ALUOp"] = '00'  # ALU performs addition

    elif opcode == '000100':  # beq instruction
        control_signals["RegDst"] = None
        control_signals["ALUSrc"] = 0
        control_signals["MemtoReg"] = None
        control_signals["RegWrite"] = 0
        control_signals["MemRead"] = 0
        control_signals["MemWrite"] = 0
        control_signals["Branch"] = 1
        control_signals["Jump"] = 0
        control_signals["ALUOp"] = '01'  # ALU performs subtraction

    elif opcode == '000010':  # j instruction
        control_signals["RegDst"] = None
        control_signals["ALUSrc"] = None
        control_signals["MemtoReg"] = None
        control_signals["RegWrite"] = 0
        control_signals["MemRead"] = 0
        control_signals["MemWrite"] = 0
        control_signals["Branch"] = 0
        control_signals["Jump"] = 1
        control_signals["ALUOp"] = None

    if opcode == '000000':  # R-type instructions
        # Decode R-type instructions
        read_reg1 = rs
        read_reg2 = rt
        write_reg = rd
        if funct == funct_dict['add']:  # Add
            reg_values[write_reg] = reg_values[read_reg1] + \
                reg_values[read_reg2]
        elif funct == funct_dict['sub']:  # Subtract
            reg_values[write_reg] = reg_values[read_reg1] - \
                reg_values[read_reg2]
        elif funct == funct_dict['and']:  # Bitwise AND
            reg_values[write_reg] = reg_values[read_reg1] & reg_values[read_reg2]
        elif funct == funct_dict['or']:  # Bitwise OR
            reg_values[write_reg] = reg_values[read_reg1] | reg_values[read_reg2]
        elif funct == funct_dict['slt']:  # Set Less Than
            reg_values[write_reg] = 1 if reg_values[read_reg1] < reg_values[read_reg2] else 0

    elif opcode in opcode_dict.values():  # I-type instructions
        immediate_sign = int(immediate, 2)
        if immediate[0] == '1':
            immediate_sign -= (2**32)  # Handle signed immediate
        # Decode I-type instructions
        if opcode == opcode_dict['addi']:  # Add immediate
            reg_values[rt] = reg_values[rs] + immediate_sign
        elif opcode == opcode_dict['lw']:  # Load word
            data_address = reg_values[rs] + immediate_sign  # Effective address
            reg_values[rt] = data_memory[data_address]  # Load word from memory
        # elif opcode == opcode_dict['beq']:  # Branch if equal
        #     if reg_values[rs] == reg_values[rt]:
        #         pc_offset = immediate << 2  # Branch offset is immediate * 4
        #         return pc_offset  # Adjust the program counter
        elif opcode == opcode_dict['j']:  # J-type instructions (Jump)
            # Target address is 26 bits shifted left by 2
            target_address = int(instruction[6:], 2) << 2
            return target_address - pc_start  # Return the offset to jump to

    return None  # No need to change PC if there's no branch or jump


def simulate_mips():
    itr = 0
    while itr < len(instruction_memory):
        # Fetch 32-bit instruction from memory
        instruction = instruction_memory[itr:itr+32]
        print(f"Executing instruction at itr={itr}: {instruction}")

        # Decode and execute the instruction
        pc_offset = decode_and_execute(instruction, (itr//4)+pc_start)

        # Update program counter
        if pc_offset is not None:
            itr += pc_offset*8
        else:
            # Move to the next instruction (each instruction is 32 bits)
            itr += 32

# # Instruction Decoding
# def decode_and_execute(instruction):
#     opcode = instruction[0:6]  # First 6 bits are the opcode
#     if opcode == '000000':  # R-type instructions
#         rs = instruction[6:11]
#         rt = instruction[11:16]
#         rd = instruction[16:21]
#         shamt = instruction[21:26]  # shift amount (not used in your current instructions)
#         funct = instruction[26:32]  # Last 6 bits are the function code

#         # Decode R-type instructions
#         if funct == funct_dict['add']:  # Add
#             reg_values[rd] = reg_values[rs] + reg_values[rt]
#         elif funct == funct_dict['sub']:  # Subtract
#             reg_values[rd] = reg_values[rs] - reg_values[rt]
#         elif funct == funct_dict['and']:  # Bitwise AND
#             reg_values[rd] = reg_values[rs] & reg_values[rt]
#         elif funct == funct_dict['or']:  # Bitwise OR
#             reg_values[rd] = reg_values[rs] | reg_values[rt]
#         elif funct == funct_dict['slt']:  # Set Less Than
#             reg_values[rd] = 1 if reg_values[rs] < reg_values[rt] else 0

#     elif opcode in opcode_dict.values():  # I-type instructions
#         rs = instruction[6:11]
#         rt = instruction[11:16]
#         imm = instruction[16:32]  # Last 16 bits are the immediate value
#         immediate = int(imm, 2) if imm[0] == '0' else -(int(imm, 2) ^ 0xFFFF) - 1  # Handle signed immediate

#         # Decode I-type instructions
#         if opcode == opcode_dict['addi']:  # Add immediate
#             reg_values[rt] = reg_values[rs] + immediate
#         elif opcode == opcode_dict['lw']:  # Load word
#             address = reg_values[rs] + immediate  # Effective address
#             reg_values[rt] = data_memory.get(address, 0)  # Load word from memory
#         elif opcode == opcode_dict['beq']:  # Branch if equal
#             if reg_values[rs] == reg_values[rt]:
#                 pc_offset = immediate << 2  # Branch offset is immediate * 4
#                 return pc_offset  # Adjust the program counter
#         elif opcode == opcode_dict['j']:  # J-type instructions (Jump)
#             target_address = int(instruction[6:], 2) << 2  # Target address is 26 bits shifted left by 2
#             return target_address - pc_start  # Return the offset to jump to

#     return None  # No need to change PC if there's no branch or jump


# def simulate_mips():
#     itr = 0
#     while itr < len(instruction_memory):
#         # Fetch 32-bit instruction from memory
#         instruction = instruction_memory[itr:itr+32]
#         print(f"Executing instruction at itr={itr}: {instruction}")

#         # Decode and execute the instruction
#         pc_offset = decode_and_execute(instruction)

#         # Update program counter
#         if pc_offset is not None:
#             itr += pc_offset*8
#         else:
#             itr += 32  # Move to the next instruction (each instruction is 32 bits)


# # After parsing, simulate the instructions
# simulate_mips()

# # Output the final state of registers and data memory
# print("Final Register Values:", reg_values)
# print("Final Data Memory:", data_memory)

# Example usage
file_path = 'example.asm'  # Path to your asm file
parse_asm_file(file_path)

# Output data_memory and instruction_binaries
print("Label_memory:", label_mem, "\n")
print("Data Memory:", data_memory, "\n")
instruction_memory_parts = [instruction_memory[i:i+32]
                            for i in range(0, len(instruction_memory), 32)]
for instruction in instruction_memory_parts:
    print(f"{int(instruction, 2):08x}")
