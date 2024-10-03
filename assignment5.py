import re

#region definations
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

#register values
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
filled = int(0)
data_memory = {}

#define label mem
label_mem = {}

# define program counter
pc_start = 4194304
pc = pc_start

#define instruction memory
instruction_memory = ""

#instrunction type
instruction_type = {
    # R-type instructions
    'add': 'R-type',
    'sub': 'R-type',
    'and': 'R-type',
    'or': 'R-type',
    'slt': 'R-type',
    
    # I-type instructions
    'addi': 'I-type',    # Add immediate
    'lw': 'I-type',      # Load word
    'beq': 'I-type',     # Branch if equal

    # J-type instructions
    'j': 'J-type',       # Jump
}


#instruction Opcode mapping
opcode_dict = {
    # I-type instructions
    'addi': '001000',   # Add immediate
    'lw': '100011',     # Load word
    'beq': '000100',    # Branch if equal
    
    # J-type instructions
    'j': '000010',      # Jump
}

# instruction func section mapping
funct_dict = {
    'add': '100000',    # Addition
    'sub': '100010',    # Subtraction
    'and': '100100',    # Bitwise AND
    'or': '100101',     # Bitwise OR
    'slt': '101010',    # Set less than
}

#endregion


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
                filled = 4-filled%4
                label_mem[current_label] = mem_start_address+filled
                data_memory[mem_start_address+filled] = value
                filled += 4
                current_label = None

            elif '.float' in line:
                # Store a single floating-point value
                value = float(line.split('.float')[1].strip())
                filled += 4 - filled%4
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
                label_mem[current_label] = mem_start_address+filled  # Reserve with '0' as placeholders
                filled += size
                current_label = None


# Parse .text section
def parse_text_section(lines):
    text_section = True
    itr = pc_start
    for line in lines:
        # Remove inline comments and strip extra spaces
        line = re.sub(r'#.*', '', line).strip()

        if ':' in line:
            line = line.split(':',1)[1].strip()  # Remove everything before and including the first colon

        if not line:
            continue

        elif text_section:
            tokens = re.split(r'[,\s]+', line)
            tokens = [token for token in tokens if token]
            instruction = tokens[0]
            if instruction in opcode_dict:  # I-type or J-type instruction
                opcode = opcode_dict[instruction]
                if(instruction == "lw"):
                    immediate = ""
                    rs = ""
                    rt = reg_addressMap[tokens[1]]
                    #case: lw $t1, -100($t0)
                    if re.match(r'[-]?\d+\(\$\w+\)', tokens[2]):
                        match = re.match(r'([-]?\d+)\((\$\w+)\)', tokens[2])
                        immediate = bin(int(match.group(1)) & 0xFFFF)[2:].zfill(16)  # Immediate value
                        rs = reg_addressMap[match.group(2)]  # Base register
    
                    # Case: lw $t1, ($t2)
                    elif re.match(r'\(\$\w+\)', tokens[2]):
                        immediate = "0000000000000000"  # Zero offset
                        rs = reg_addressMap[re.match(r'\(\$(\w+)\)', tokens[2]).group(1)]  # Base register
    
                    # Case: lw $t1, label
                    elif tokens[2] in label_mem:
                        reg_values['00001'] = format(mem_start_address,'032b')  # Label address as immediate
                        immediate = format(label_mem[tokens[2]] - mem_start_address, '032b')
                        rs = "00001"  # No base register, use 0
                    
                    instruction_memory += opcode+rs+rt+immediate
                    itr = itr+4
                
                if(instruction == "beq"):
                    # Handle the case of beq $t1, $t2, label (Register-Register)
                    immediate=""
                    if re.match(r'\$\w+', tokens[2]):  # Check if second operand is a register
                        rs = reg_addressMap[tokens[1]]  # First register ($t1)
                        rt = reg_addressMap[tokens[2]]  # Second register ($t2)
                        label = tokens[3]               # The label
                        immediate = format(int((label_mem[label]-itr-4)/4),'016b')

                    # Handle the case of beq $t1, immediate, label (Register-Immediate)
                    elif re.match(r'-?\d+', tokens[2]):  # Check if second operand is an immediate
                        rs = reg_addressMap[tokens[1]]  # First register ($t1)
                        reg_values['00001'] = int(tokens[2])  #compare value
                        rt = reg_addressMap["$at"]
                        immediate = format(int((label_mem[tokens[3]]-itr-4)/4),'016b')
                    instruction_memory += opcode+rs+rt+immediate
                    itr = itr+4
                
                if(instruction == "addi"):

                rs = reg_addressMap[tokens[1]]
                rt = reg_addressMap[tokens[2]]
                imm = bin(int(tokens[3]))[2:].zfill(16)
                insturction_memory += opcode + rs + rt + imm
            elif instruction in funct_dict:  # R-type instruction
                opcode = '000000'
                rs = reg_addressMap[tokens[2]]
                rt = reg_addressMap[tokens[0]]

# Subroutine Address (Completed)
def subroute_add(lines):
  itr = pc_start
  for line in lines:
      line = re.sub(r'#.*', '', line).strip()
      if not line:
          continue
      if ':' in line :
           parts = line.split(':')
           label = parts[0].strip()
           label_mem[label] = itr
           if parts[1].strip()=="":
               itr -= 4
      itr += 4

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

        print(data_section_lines)
        print(text_section_lines)

        # Parse .data section
        parse_data_section(data_section_lines)
        
        # Parse .text section
        subroute_add(text_section_lines)
        parse_text_section(text_section_lines)


# Example usage
file_path = 'example.asm'  # Path to your asm file
parse_asm_file(file_path)

# Output data_memory and instruction_binaries
print("Label_memory:", label_mem)
print("Data Memory:", data_memory)