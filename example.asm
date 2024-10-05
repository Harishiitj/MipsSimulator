.data
    space: .space 12
    val1: .word 5
    val2: .word 5
    val3: .word 5
    val4: .word 6
  
.text
    lw $t0, val4
    lw $t1, val2
    addi $t2, $t0, 10
    beq $t0, 100, equal_case
    sub $t3, $t0, $t1
    j end
equal_case:
    add $t3, $t0, $t1
    
    end:
