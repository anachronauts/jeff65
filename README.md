# Gold

Gold is a programming language (and cross-compiler) for the Commodore 64. Gold's
syntax is inspired by Lua. The compiler is implemented in Python 3 and generates
6502 assembly code. For now, the recommended assembler is ca65 (part of cc65),
which is capable of producing .d64 disk images.

Gold-lang is not associated with the Gold parser framework.

    usage: python3 -m compiler [-h] input_file

    positional arguments:
      input_file  the file to compile

    optional arguments:
      -h, --help  show this help message and exit

These are the tokens needed to parse an expression (highest binding power first):

    numeric_literal[value], identifier[name], string_literal[value]
    punctuation_open_bracket["["], punctiation_close_bracket["]"]
    punctuation_open_paren["("], punctuation_close_paren[")"]
    /* TODO: pointer operators? */
    operator_bw_and["&&&", "bitand"]
    oeprator_bw_or["|||", "bitor"]
    operator_bw_xor["bitxor"]
    operator_bw_lshift["<<", "lshift"]
    operator_bw_rshift[">>", "rshift"]
    operator_div["/"], operator_mult["*"]
    operator_add["+"], operator_minus["-"]
    operator_equals["==", "equals"], operator_gt[">"], operator_lt["<"], operator_gte[">="], operator_lte["<="]
    operator_not["not"]
    operator_and["and"]
    operator_or["or"]

These are the other tokens we will have (unsorted):

    keyword_use["use"]
    keyword_isr["isr"]
    keyword_fun["fun"]
    /* keyword_struct["struct"] */
    keyword_let["let"]
    keyword_while["while"]
    keyword_for["for"]
    keyword_do["do"]
    keyword_end["end"]
    keyword_endfun["endfun"]
    keyword_endisr["endisr"]
    /* keyword_endstruct["endstruct"] */
    keyword_if["if"]
    keyword_elseif["elseif"]
    keyword_else["else"]
    keyword_then["then"]
    keyword_in["in"]
    keyword_mut["mut"]
    keyword_stash["stash"]
    keyword_byte["byte"]
    keyword_dword["dword"]
    keyword_qword["qword"]
    /* punctiation_open_brace["{"] */
    /* punctiation_close_brace["}"] */
    punctuation_colon[":"]
    operator_assign["="]
    comment[value]
    whitespace[value]
    eof

# Blum

Blum is an upcoming fantasy rouge-like (written in Gold) for the Commodore 64.