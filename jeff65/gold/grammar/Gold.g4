parser grammar Gold;

tokens {
    // simple tokens
    IDENTIFIER, NUMERIC, STRING,

    // arithmetic operators
    OPERATOR_PLUS, OPERATOR_MINUS, OPERATOR_TIMES, OPERATOR_DIVIDE,

    // logical operators
    OPERATOR_NOT, OPERATOR_AND, OPERATOR_OR,

    // bitwise operators
    OPERATOR_SHR, OPERATOR_SHL, OPERATOR_BITNOT, OPERATOR_BITAND,
    OPERATOR_BITOR, OPERATOR_BITXOR,

    // comparison operators
    OPERATOR_NE, OPERATOR_EQ, OPERATOR_LE, OPERATOR_GE, OPERATOR_LT,
    OPERATOR_GT,

    // assignment operators
    OPERATOR_ASSIGN, OPERATOR_ASSIGN_INC, OPERATOR_ASSIGN_DEC,

    // member access operators
    OPERATOR_DOT,

    // pointer operators
    OPERATOR_DEREF, OPERATOR_REF,

    // statement keywords
    STMT_ASM, STMT_CONSTANT, STMT_FOR, STMT_FUN, STMT_IF, STMT_ISR, STMT_LET,
    STMT_RETURN, STMT_USE, STMT_WHILE,

    // storage classes
    STORAGE_MUT, STORAGE_STASH,

    // assorted punctuation
    PUNCT_DO, PUNCT_ELSE, PUNCT_ELSEIF, PUNCT_END, PUNCT_ENDFUN, PUNCT_ENDISR,
    PUNCT_IN, PUNCT_THEN, PUNCT_TO, PUNCT_COLON, PUNCT_SEMICOLON, PUNCT_COMMA,
    PUNCT_ARROWR,

    // delimiters
    PAREN_OPEN, PAREN_CLOSE, BRACKET_OPEN, BRACKET_CLOSE, BRACE_OPEN,
    BRACE_CLOSE,

    // dummy tokens for internal lexer use.
    STRING_DELIM, COMMENT_OPEN, COMMENT_CLOSE, COMMENT_TEXT, WHITESPACE, MYSTERY
}

expr : PAREN_OPEN expr PAREN_CLOSE  # ExprParen
     | expr OPERATOR_DOT member=IDENTIFIER  # ExprMember
     | expr BRACKET_OPEN expr BRACKET_CLOSE  # ExprIndex
     | fun=expr PAREN_OPEN (args+=expr (PUNCT_COMMA args+=expr)*)? PAREN_CLOSE  # ExprFunCall
     | OPERATOR_DEREF expr  # ExprDeref
     | OPERATOR_MINUS expr  # ExprNegation
     | expr OPERATOR_BITNOT expr  # ExprBitNot
     | expr OPERATOR_BITAND expr  # ExprBitAnd
     | expr OPERATOR_BITOR expr  # ExprBitOr
     | expr OPERATOR_BITXOR expr  # ExprBitXor
     | expr op=( OPERATOR_SHL | OPERATOR_SHR ) expr  # ExprBitShift
     | expr op=( OPERATOR_TIMES | OPERATOR_DIVIDE ) expr  # ExprProduct
     | expr op=( OPERATOR_PLUS | OPERATOR_MINUS ) expr  # ExprSum
     | expr op=( OPERATOR_EQ | OPERATOR_NE
               | OPERATOR_LE | OPERATOR_GE
               | OPERATOR_LT | OPERATOR_GT) expr  # ExprCompare
     | value=NUMERIC  # ExprNumber
     | name=IDENTIFIER  # ExprId
     ;

array : BRACKET_OPEN (expr (PUNCT_COMMA expr)*)? BRACKET_CLOSE ;

string : (s+=STRING)+ ;

storage : storage_class=(STORAGE_MUT | STORAGE_STASH) ;

typeId : name=IDENTIFIER  # TypePrimitive
       | OPERATOR_REF BRACKET_OPEN storage? typeId BRACKET_CLOSE  # TypeSlice
       | OPERATOR_REF storage? typeId  # TypePointer
       | BRACKET_OPEN storage? typeId PUNCT_SEMICOLON
           (expr | rangeTo) BRACKET_CLOSE  # TypeArray
       ;

rangeTo : expr PUNCT_TO expr ;

declaration : name=IDENTIFIER PUNCT_COLON typeId ;

stmtConstant : STMT_CONSTANT declaration OPERATOR_ASSIGN ( expr | array ) ;

stmtUse : STMT_USE unitId=IDENTIFIER ;

stmtLet : STMT_LET storage? declaration
          OPERATOR_ASSIGN
          ( expr | array | string ) ;

stmtWhile : STMT_WHILE expr PUNCT_DO block PUNCT_END ;

stmtFor : STMT_FOR declaration PUNCT_IN ( rangeTo | expr )
          PUNCT_DO block PUNCT_END ;

stmtIf : STMT_IF expr PUNCT_THEN block
         ( PUNCT_ELSEIF block )*
         ( PUNCT_ELSE block )?
         PUNCT_END ;

stmtAsm : STMT_ASM string PUNCT_DO string PUNCT_END ;

stmtIsr : STMT_ISR IDENTIFIER block PUNCT_ENDISR ;

stmtFun : STMT_FUN name=IDENTIFIER
          PAREN_OPEN ( args+=declaration ( PUNCT_COMMA args+=declaration )* )? PAREN_CLOSE
          ( PUNCT_ARROWR ret=typeId )?
          block
          PUNCT_ENDFUN ;

stmtReturn : STMT_RETURN expr? ;

stmtAssign : expr OPERATOR_ASSIGN expr  # stmtAssignVal
           | expr OPERATOR_ASSIGN_INC expr  # stmtAssignInc
           | expr OPERATOR_ASSIGN_DEC expr  # stmtAssignDec
           ;

block : ( stmtAsm
        | stmtConstant
        | stmtFor
        | stmtIf
        | stmtLet
        | stmtReturn
        | stmtWhile
        | stmtAssign  // these need to be last
        | expr
        )* ;

unit : ( stmtConstant
       | stmtIsr
       | stmtLet
       | stmtUse
       | stmtFun
       )* EOF ;