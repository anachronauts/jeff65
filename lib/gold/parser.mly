(* jeff65 gold-syntax AST
   Copyright (C) 2019  jeff65 maintainers
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>. *)

%{

open Ast

%}

(* control tokens *)
%token EOF
(* %token STRING_DELIM *)
(* %token COMMENT_OPEN *)
(* %token COMMENT_CLOSE *)

(* literals tokens *)
%token <string> IDENTIFIER
%token <string> NUMERIC
(* %token <string> STRING *)
(* %token <string> STRING_ESCAPE *)

(* arithmetic operators *)
%token OPERATOR_PLUS
%token OPERATOR_MINUS
%token OPERATOR_TIMES
%token OPERATOR_DIVIDE

(* logical operators *)
%token OPERATOR_NOT
%token OPERATOR_AND
%token OPERATOR_OR

(* bitwise operators *)
%token OPERATOR_SHR
%token OPERATOR_SHL
%token OPERATOR_BITNOT
%token OPERATOR_BITAND
%token OPERATOR_BITOR
%token OPERATOR_BITXOR

(* comparison operators *)
%token OPERATOR_NE
%token OPERATOR_EQ
%token OPERATOR_LE
%token OPERATOR_GE
%token OPERATOR_LT
%token OPERATOR_GT

(* assignment operators *)
%token OPERATOR_ASSIGN
%token OPERATOR_ASSIGN_INC
%token OPERATOR_ASSIGN_DEC

(* member access operators *)
%token OPERATOR_DOT

(* pointer operators *)
%token OPERATOR_DEREF
%token OPERATOR_REF

(* statement keywords *)
%token STMT_CONSTANT
%token STMT_FOR
%token STMT_FUN
%token STMT_IF
%token STMT_ISR
%token STMT_LET
%token STMT_RETURN
%token STMT_USE
%token STMT_WHILE

(* storage classes *)
%token STORAGE_MUT
%token STORAGE_STASH

(* assorted punctuation *)
%token PUNCT_DO
%token PUNCT_ELSE
%token PUNCT_ELSEIF
%token PUNCT_END
%token PUNCT_ENDFUN
%token PUNCT_ENDISR
%token PUNCT_IN
%token PUNCT_THEN
%token PUNCT_TO
%token PUNCT_COLON
%token PUNCT_SEMICOLON
%token PUNCT_COMMA
%token PUNCT_ARROWR

(* delimiters *)
%token PAREN_OPEN
%token PAREN_CLOSE
%token BRACKET_OPEN
%token BRACKET_CLOSE
(* %token BRACE_OPEN *)
(* %token BRACE_CLOSE *)

%nonassoc STMT
%nonassoc OPERATOR_ASSIGN OPERATOR_ASSIGN_INC OPERATOR_ASSIGN_DEC STMT_RETURN
%nonassoc IDENTIFIER NUMERIC
%left OPERATOR_OR
%left OPERATOR_AND
%right OPERATOR_NOT
%left OPERATOR_EQ OPERATOR_NE OPERATOR_LE OPERATOR_GE OPERATOR_LT OPERATOR_GT
%left OPERATOR_PLUS OPERATOR_MINUS
%left OPERATOR_TIMES OPERATOR_DIVIDE
%left OPERATOR_SHL OPERATOR_SHR
%left OPERATOR_BITXOR
%left OPERATOR_BITOR
%left OPERATOR_BITAND
%right OPERATOR_BITNOT OPERATOR_DEREF OPERATOR_REF OPERATOR_UMINUS
%right OPERATOR_DOT
%nonassoc PAREN_OPEN
%nonassoc BRACKET_OPEN

%start <Ast.Node.t> unit
%%

let expr :=
  | ~ = delimited(PAREN_OPEN, expr, PAREN_CLOSE); <>
  | ~ = expr; OPERATOR_DOT; m = IDENTIFIER;
    { `Member_access (expr, m) |> Spanning.loc $loc }
  | t = expr; a = delimited(BRACKET_OPEN, expr, BRACKET_CLOSE);
    { `Subscript (t, a) |> Spanning.loc $loc }
  | target = expr; args = delimited(PAREN_OPEN, alist, PAREN_CLOSE);
    { `Call { ValCall.target; args } |> Spanning.loc $loc }
  | OPERATOR_REF; ~ = expr;
    { `Ref expr |> Spanning.loc $loc }
  | OPERATOR_DEREF; ~ = expr;
    { `Deref expr |> Spanning.loc $loc }
  | OPERATOR_MINUS; ~ = expr;
    { `Negate expr |> Spanning.loc $loc } %prec OPERATOR_UMINUS
  | OPERATOR_BITNOT; ~ = expr;
    { `Bit_not expr |> Spanning.loc $loc }
  | OPERATOR_NOT; ~ = expr;
    { `Log_not expr |> Spanning.loc $loc }
  | l = expr; OPERATOR_BITAND; r = expr;
    { `Bit_and (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_BITOR; r = expr;
    { `Bit_or (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_BITXOR; r = expr;
    { `Bit_xor (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_SHL; r = expr;
    { `Shl (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_SHR; r = expr;
    { `Shr (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_TIMES; r = expr;
    { `Mul (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_DIVIDE; r = expr;
    { `Div (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_PLUS; r = expr;
    { `Add (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_MINUS; r = expr;
    { `Sub (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_EQ; r = expr;
    { `Cmp_eq (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_NE; r = expr;
    { `Cmp_ne (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_LE; r = expr;
    { `Cmp_le (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_GE; r = expr;
    { `Cmp_ge (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_LT; r = expr;
    { `Cmp_lt (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_GT; r = expr;
    { `Cmp_gt (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_OR; r = expr;
    { `Log_or (l, r) |> Spanning.loc $loc }
  | l = expr; OPERATOR_AND; r = expr;
    { `Log_and (l, r) |> Spanning.loc $loc }
  | id = IDENTIFIER; { `Identifier id |> Spanning.loc $loc }
  | num = NUMERIC; { `Numeric num |> Spanning.loc $loc }

let alist :=
  | ~ = separated_list(PUNCT_COMMA, expr); <>

let array :=
  | alist = delimited(BRACKET_OPEN, alist, BRACKET_CLOSE);
    { `Array alist |> Spanning.loc $loc }

let storage :=
  | { Auto }
  | STORAGE_MUT; { Mut }
  | STORAGE_STASH; { Stash }

let range :=
  | f = expr; PUNCT_TO; t = expr; { (f, t) }

let range_or_upper :=
  | ~ = expr; { (`Numeric "0", expr) }
  | ~ = range; <>

let range_or_expr :=
  | ~ = expr; <StmtFor.Iter>
  | (f, t) = range; <StmtFor.Range>

let inner_type_id :=
  | id = IDENTIFIER; <Typename.Primitive>
  | OPERATOR_REF; s = storage; p = inner_type_id;
    { Typename.Ref { RefType.ty = p; storage = s } }
  | OPERATOR_REF; BRACKET_OPEN; s = storage; t = inner_type_id; BRACKET_CLOSE;
    { Typename.Slice { SliceType.ty = t; storage = s } }

let type_id :=
  | ~ = inner_type_id; <>
  | BRACKET_OPEN; s = storage; t = inner_type_id; PUNCT_SEMICOLON;
    r = range_or_upper; BRACKET_CLOSE;
    { Typename.Array { ArrayType.ty = t; storage = s; range = r } }

let declaration :=
  | name = IDENTIFIER; PUNCT_COLON; ty = type_id; { { Decl.name; ty } }

let expr_or_array ==
  | ~ = expr; <>
  | ~ = array; <>

let stmt_constant :=
  | STMT_CONSTANT; d = declaration; OPERATOR_ASSIGN; e = expr_or_array;
    { `Stmt_constant { StmtConstant.decl = d; value = e } |> Spanning.loc $loc }
    %prec STMT

let stmt_use :=
  | STMT_USE; name = IDENTIFIER;
    { `Stmt_use { StmtUse.name } |> Spanning.loc $loc }

let stmt_let :=
  | STMT_LET; s = storage; d = declaration; OPERATOR_ASSIGN; e = expr_or_array;
    { `Stmt_let { StmtLet.decl = d; storage = s; value = e } |> Spanning.loc $loc }
    %prec STMT

let do_block :=
  | PUNCT_DO; ~ = body*; PUNCT_END; <>

let stmt_while :=
  | STMT_WHILE; cond = expr; body = do_block;
    { `Stmt_while { StmtWhile.cond; body } |> Spanning.loc $loc }

let stmt_for :=
  | STMT_FOR; var = declaration; PUNCT_IN; range = range_or_expr; body = do_block;
    { `Stmt_for { StmtFor.var; range; body } |> Spanning.loc $loc }

let branch_elseif :=
  | PUNCT_ELSEIF; cond = expr; PUNCT_THEN; body = body*;
    { { StmtIf.cond = cond; body = body } }

let branch_else :=
  | PUNCT_ELSE; body = body*;
    { { StmtIf.cond = `Boolean true; body = body } }

let stmt_if :=
  | STMT_IF; cond = expr; PUNCT_THEN; body0 = body*;
    branchn = branch_elseif*;
    branchf = branch_else;
    PUNCT_END;
    {
      let branch0 = { StmtIf.cond; body = body0 } in
      let branches = branch0 :: (branchn @ [branchf]) in
      (`Stmt_if branches) |> Spanning.loc $loc
    }

let stmt_isr :=
  | STMT_ISR; name = IDENTIFIER; body = body*; PUNCT_ENDISR;
    { `Stmt_isr { StmtIsr.name; body } |> Spanning.loc $loc }

let stmt_expr :=
  | ~ = expr;
    { `Stmt_expr expr |> Spanning.loc $loc } %prec STMT

let plist := ~ = separated_list(PUNCT_COMMA, declaration); <>

let stmt_fun :=
  | STMT_FUN; name = IDENTIFIER; params = delimited(PAREN_OPEN, plist, PAREN_CLOSE);
    body = body*; PUNCT_ENDFUN;
    { `Stmt_fun { StmtFun.name
                ; return = Typename.Void
                ; params; body }
      |> Spanning.loc $loc }
  | STMT_FUN; name = IDENTIFIER; params = delimited(PAREN_OPEN, plist, PAREN_CLOSE);
    PUNCT_ARROWR; return = type_id;
    body = body*; PUNCT_ENDFUN;
    { `Stmt_fun { StmtFun.name; return; params; body }
      |> Spanning.loc $loc }

let stmt_return :=
  | STMT_RETURN; ~ = expr;
    { `Stmt_return (Some expr) |> Spanning.loc $loc }
  | STMT_RETURN;
    { `Stmt_return None |> Spanning.loc $loc }

let stmt_assign :=
  | lvalue = expr; OPERATOR_ASSIGN; rvalue = expr;
    { `Stmt_assign { StmtAssign.lvalue; rvalue } |> Spanning.loc $loc }
  | lvalue = expr; OPERATOR_ASSIGN_INC; rvalue = expr;
    { `Stmt_assign { StmtAssign.lvalue; rvalue = `Add (lvalue, rvalue) }
      |> Spanning.loc $loc }
  | lvalue = expr; OPERATOR_ASSIGN_DEC; rvalue = expr;
    { `Stmt_assign { StmtAssign.lvalue ; rvalue = `Sub (lvalue, rvalue) }
      |> Spanning.loc $loc }

let common_block ==
  | ~ = stmt_constant; <>
  | ~ = stmt_use; <>
  | ~ = stmt_let; <>

let body :=
  | ~ = common_block; <>
  | ~ = stmt_while; <>
  | ~ = stmt_for; <>
  | ~ = stmt_expr; <>
  | ~ = stmt_if; <>
  | ~ = stmt_return; <>
  | ~ = stmt_assign; <>

let toplevel :=
  | ~ = common_block; <>
  | ~ = stmt_fun; <>
  | ~ = stmt_isr; <>

let unit :=
  | body = toplevel*; EOF; { `Unit body |> Spanning.loc $loc }

