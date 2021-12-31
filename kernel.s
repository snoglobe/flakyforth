    PROCESSOR 6502
    MAC _if
        PLA
        CMP #0
        BNE {1}
    ENDM
    MAC push
        LDA {1}
        PHA
    ENDM

    seg.u	zeropage
	org $e0
EQSTOR  ds 1
OPSTOR  ds 1
	
    seg		code
	org		$c00

; -- code --
;cd


; -- subroutines --

true:
    LDA #1
    PHA
    RTS

false:
    LDA #0
    PHA
    RTS

add:
    CLC
    PLA
    TAX
    PLA
    STX OPSTOR
    ADC OPSTOR
    PHA
    RTS

sub:
    SEC
    PLA
    TAX
    PLA
    STX OPSTOR
    SBC OPSTOR
    PHA
    RTS

dup:
    PLA ; pull into A
    TAX ; put A into X (store it for later)
    PHA ; push A to the stack (push it back)
    TXA ; put X into A (restore the value of A)
    PHA ; push A to the stack (put it in again)
    RTS

drop:
    PLA ; pull into A
    LDA #0 ; set A to 0
    RTS

swap:
    PLA
    TAX
    PLA
    TAY
    TXA
    PHA
    TYA
    PHA
    RTS

over:
    PLA
    TAX
    PLA
    TAY
    TYA
    PHA
    TXA
    PHA
    TYA
    PHA
    RTS

emit:
    PLA
    JSR $FDED
    RTS

eq:
    PLA
    STA EQSTOR
    PLA
    CMP EQSTOR
    BEQ true
    BNE false
    RTS
    
;sr