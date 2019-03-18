  jsr clear
  jsr loadirq

.proc irq
  sta atemp+1
  stx xtemp+1
  sty ytemp+1

  lda #$ff
  sta $d019

  boff = $01be
  hoff = $0400 + boff
  coff = $d800 + boff
  ldx #$00
  lda text,x
copy:
  jsr conv
  sta hoff,x
col:
  lda #$01
  sta coff,x
  inx
  lda text,x
  bne copy

  inc frame
  lda #$7
  cmp frame
  bne done
  lda #$0
  sta frame


  inc col+1
  lda #$9
  cmp col+1
  bne done
  lda #$1
  sta col+1

done: 


atemp:
  lda #$00
xtemp:
  ldx #$00
ytemp:
  ldy #$00

  rti

frame:  .byte $0
.endproc

.proc conv
  pha
  .repeat 5
    lsr a
  .endrepeat
  tay
  pla
  clc
  adc choff,y
  rts
.endproc

.proc clear
  lda #$00
  sta $d020
  sta $d021
  tax
  lda #$20
loop:
  sta $0400, x
  sta $0500, x
  sta $0600, x
  sta $0700, x
  dex
  bne loop
  rts
.endproc

.proc loadirq
  sei                           ; disable interrupts

  lda #$7f
  sta $dc0d                     ; disable timer interrupts
  sta $dd0d

  lda $dc0d                     ; reading these clears pending irqs
  lda $dd0d

  lda #$01                      ; ask the VIC-II to generate the raster
  sta $d01a                     ; interrupt for us
  lda #$00                      ; choose rasterline (lower 8 bits)
  sta $d012
  lda #$1b                      ; choose rasterline (bit 9)
  sta $d011

  lda #$35                      ; disable BASIC and KERNAL rom
  sta $01

  lda #<irq                     ; store the ISR in the appropriate place
  sta $fffe
  lda #>irq
  sta $ffff

  cli                           ; re-enable interrupts
  jmp *                         ; prevent from returning
.endproc

.rodata
choff:  .byte $80,$00,$c0,$e0,$40,$c0,$80,$80
text:   .asciiz "hello world! hello friends!"
