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

open! Containers
open! Astring
open Jeff65_kernel.Ast
open Syntax

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

%start <(Syntax.Form.t, Syntax.Tag.t) Jeff65_kernel.Ast.Node.t> unit
%%

let expr :=
  | ~ = delimited(PAREN_OPEN, expr, PAREN_CLOSE); <>
  | ~ = expr; OPERATOR_DOT; m = IDENTIFIER;
    { Node.create `Member_access
        ~children:[ `Target, expr
                  ; `Member, identifier m ~span:$loc(m)]
        ~span:$loc }
  | t = expr; a = delimited(BRACKET_OPEN, expr, BRACKET_CLOSE);
    { Node.create `Subscript ~children:[`Target, t; `Of, a] ~span:$loc }
  | target = expr; args = delimited(PAREN_OPEN, alist, PAREN_CLOSE);
    { let args = List.map (fun a -> (`Elem, a)) args in
      let args = Node.create `A_list ~children:args ~span:$loc(args) in
      Node.create `Call ~children:[`Target, target; `Of, args] ~span:$loc }
  | OPERATOR_REF; ~ = expr;
    { op_prefix `Refer expr ~span:$loc }
  | OPERATOR_DEREF; ~ = expr;
    { op_prefix `Deref expr ~span:$loc }
  | OPERATOR_MINUS; ~ = expr;
    { op_prefix `Negate expr ~span:$loc } %prec OPERATOR_UMINUS
  | OPERATOR_BITNOT; ~ = expr;
    { op_prefix `Bit_not expr ~span:$loc }
  | OPERATOR_NOT; ~ = expr;
    { op_prefix `Log_not expr ~span:$loc }
  | l = expr; OPERATOR_BITAND; r = expr;
    { op_binary `Bit_and l r ~span:$loc }
  | l = expr; OPERATOR_BITOR; r = expr;
    { op_binary `Bit_or l r ~span:$loc }
  | l = expr; OPERATOR_BITXOR; r = expr;
    { op_binary `Bit_xor l r ~span:$loc }
  | l = expr; OPERATOR_SHL; r = expr;
    { op_binary `Shl l r ~span:$loc }
  | l = expr; OPERATOR_SHR; r = expr;
    { op_binary `Shr l r ~span:$loc }
  | l = expr; OPERATOR_TIMES; r = expr;
    { op_binary `Mul l r ~span:$loc }
  | l = expr; OPERATOR_DIVIDE; r = expr;
    { op_binary `Div l r ~span:$loc }
  | l = expr; OPERATOR_PLUS; r = expr;
    { op_binary `Add l r ~span:$loc }
  | l = expr; OPERATOR_MINUS; r = expr;
    { op_binary `Sub l r ~span:$loc }
  | l = expr; OPERATOR_EQ; r = expr;
    { op_binary `Cmp_eq l r ~span:$loc }
  | l = expr; OPERATOR_NE; r = expr;
    { op_binary `Cmp_ne l r ~span:$loc }
  | l = expr; OPERATOR_LE; r = expr;
    { op_binary `Cmp_le l r ~span:$loc }
  | l = expr; OPERATOR_GE; r = expr;
    { op_binary `Cmp_ge l r ~span:$loc }
  | l = expr; OPERATOR_LT; r = expr;
    { op_binary `Cmp_lt l r ~span:$loc }
  | l = expr; OPERATOR_GT; r = expr;
    { op_binary `Cmp_gt l r ~span:$loc }
  | l = expr; OPERATOR_OR; r = expr;
    { op_binary `Log_or l r ~span:$loc }
  | l = expr; OPERATOR_AND; r = expr;
    { op_binary `Log_and l r ~span:$loc }
  | id = IDENTIFIER; { identifier id ~span:$loc }
  | num = NUMERIC; { Node.create (`Numeric num) ~span:$loc }

let alist :=
  | ~ = separated_list(PUNCT_COMMA, expr); <>

let array :=
  | alist = delimited(BRACKET_OPEN, alist, BRACKET_CLOSE);
    { let children = List.map (fun a -> (`Elem, a)) alist in
      Node.create `Array ~children ~span:$loc }

let storage :=
  | { Node.create `Storage_default ~span:$loc }
  | STORAGE_MUT; { Node.create `Storage_mut ~span:$loc }
  | STORAGE_STASH; { Node.create `Storage_stash ~span:$loc }

let range :=
  | f = expr; PUNCT_TO; t = expr; { (f, t) }

let range_or_upper :=
  | ~ = expr; { (Node.create (`Numeric "0"), expr) }
  | ~ = range; <>

let range_or_expr :=
  | ~ = expr; { Node.create `Iterable ~children:[`Of, expr] ~span:$loc }
  | (f, t) = range; { Node.create `Range ~children:[`From, f; `To, t] ~span:$loc }

let inner_type_id :=
  | id = IDENTIFIER;
    { let name = identifier id ~span:$loc(id) in
      Node.create `Type_primitive ~children:[`Name, name] ~span:$loc }
  | OPERATOR_REF; s = storage; b = inner_type_id;
    { Node.create `Type_ref ~children:[`Storage, s; `Base, b] ~span:$loc }
  | OPERATOR_REF; BRACKET_OPEN; s = storage; b = inner_type_id; BRACKET_CLOSE;
    { Node.create `Type_slice ~children:[`Storage, s; `Base, b] ~span:$loc }

let type_id :=
  | ~ = inner_type_id; <>
  | BRACKET_OPEN; s = storage; b = inner_type_id; PUNCT_SEMICOLON;
    (f, t) = range_or_upper; BRACKET_CLOSE;
    { Node.create `Type_array
        ~children:[ `Storage, s
                  ; `Base, b
                  ; `From, f
                  ; `To, t
                  ]
        ~span:$loc }

let declaration :=
  | name = IDENTIFIER; PUNCT_COLON; ty = type_id;
    { (identifier name ~span:$loc(name), ty) }

let expr_or_array ==
  | ~ = expr; <>
  | ~ = array; <>

let stmt_constant :=
  | STMT_CONSTANT; (n, t) = declaration; OPERATOR_ASSIGN; e = expr_or_array;
    { Node.create `Stmt_constant
        ~children:[ `Name, n
                  ; `Type, t
                  ; `Of, e ]
        ~span:$loc }
    %prec STMT

let stmt_use :=
  | STMT_USE; name = IDENTIFIER;
    { Node.create `Stmt_use ~children:[`Name, identifier name ~span:$loc(name)] ~span:$loc }

let stmt_let :=
  | STMT_LET; s = storage; (n, t) = declaration; OPERATOR_ASSIGN; e = expr_or_array;
    { Node.create `Stmt_let
        ~children:[ `Storage, s
                  ; `Name, n
                  ; `Type, t
                  ; `Of, e ]
        ~span:$loc }
    %prec STMT

let do_block :=
  | PUNCT_DO; body = body*; PUNCT_END;
    { block body ~span:$loc }

let stmt_while :=
  | STMT_WHILE; cond = expr; body = do_block;
    { Node.create `Stmt_while ~children:[`Cond, cond; `Body, body] ~span:$loc }

let stmt_for :=
  | STMT_FOR; (n, t) = declaration; PUNCT_IN; range = range_or_expr; body = do_block;
    { Node.create `Stmt_for
        ~children:[ `Name, n
                  ; `Type, t
                  ; `Of, range
                  ; `Body, body ]
        ~span:$loc }

let branch_elseif :=
  | PUNCT_ELSEIF; cond = expr; PUNCT_THEN; body = body*;
    { let body = block body ~span:$loc(body) in
      Node.create `Branch_if ~children:[`Cond, cond; `Body, body] ~span:$loc }

let branch_else :=
  | PUNCT_ELSE; body = body*;
    { let body = block body ~span:$loc(body) in
      Node.create `Branch_else ~children:[`Body, body] ~span:$loc }

let stmt_if :=
  | STMT_IF; cond = expr; PUNCT_THEN; body0 = body*;
    branchn = branch_elseif*;
    branchf = branch_else;
    PUNCT_END;
    { let body0 = block body0 ~span:$loc(body0) in
      let branch0 = Node.create `Branch_if
                      ~children:[`Cond, cond; `Body, body0]
                      ~span:($startpos, $endpos(body0))
      in
      let branch0 = (`Branch, branch0) in
      let branchn = List.map (fun b -> (`Branch, b)) branchn in
      let branchf = (`Branch, branchf) in
      let children = branch0 :: (branchn @ [branchf]) in
      Node.create `Stmt_if ~children ~span:$loc }

let stmt_isr :=
  | STMT_ISR; name = IDENTIFIER; body = body*; PUNCT_ENDISR;
    { let name = identifier name ~span:$loc(name) in
      let body = block body ~span:$loc(body) in
      Node.create `Stmt_isr ~children:[`Name, name; `Body, body] ~span:$loc }

let stmt_expr :=
  | ~ = expr;
    { Node.create `Stmt_expr ~children:[`Of, expr] ~span:$loc } %prec STMT

let plist := ~ = separated_list(PUNCT_COMMA, declaration); <>

let stmt_fun :=
  | STMT_FUN; name = IDENTIFIER; params = delimited(PAREN_OPEN, plist, PAREN_CLOSE);
    body = body*; PUNCT_ENDFUN;
    { let name = identifier name ~span:$loc(name) in
      let params = List.flat_map (fun (n, t) -> [`Name, n; `Type, t]) params in
      let params = Node.create `P_list ~children:params ~span:$loc(params) in
      let return = Node.create `Type_primitive ~children:[`Name, identifier "void"] in
      let ty = Node.create `Type_fun ~children:[`From, params; `To, return] in
      let body = block body ~span:$loc(body) in
      Node.create `Stmt_fun
        ~children:[ `Name, name
                  ; `Type, ty
                  ; `Body, body ]
        ~span:$loc }
  | STMT_FUN; name = IDENTIFIER; params = delimited(PAREN_OPEN, plist, PAREN_CLOSE);
    PUNCT_ARROWR; return = type_id;
    body = body*; PUNCT_ENDFUN;
    { let name = identifier name ~span:$loc(name) in
      let params = List.flat_map (fun (n, t) -> [`Name, n; `Type, t]) params in
      let params = Node.create `P_list ~children:params ~span:$loc(params) in
      let ty = Node.create `Type_fun ~children:[`From, params; `To, return] in
      let body = block body ~span:$loc(body) in
      Node.create `Stmt_fun
        ~children:[ `Name, name
                  ; `Type, ty
                  ; `Body, body ]
        ~span:$loc }

let stmt_return :=
  | STMT_RETURN; ~ = expr;
    { Node.create `Stmt_return ~children:[`Of, expr] ~span:$loc }
  | STMT_RETURN;
    { Node.create `Stmt_return ~span:$loc }

let stmt_assign :=
  | lvalue = expr; OPERATOR_ASSIGN; rvalue = expr;
    { Node.create `Stmt_assign ~children:[`Target, lvalue; `Of, rvalue] ~span:$loc }
  | lvalue = expr; OPERATOR_ASSIGN_INC; rvalue = expr;
    { let sum = Node.create `Add ~children:[`Of, lvalue; `Of, rvalue] in
      Node.create `Stmt_assign ~children:[`Target, lvalue; `Of, sum] ~span:$loc }
  | lvalue = expr; OPERATOR_ASSIGN_DEC; rvalue = expr;
    { let diff = Node.create `Sub ~children:[`Of, lvalue; `Of, rvalue] in
      Node.create `Stmt_assign ~children:[`Target, lvalue; `Of, diff] ~span:$loc }

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
  | body = toplevel*; EOF;
    { let children = List.map (fun b -> (`Body, b)) body in
      Node.create `Unit ~children ~span:$loc }

