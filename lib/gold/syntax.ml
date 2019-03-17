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

open! Containers
open! Astring
open Jeff65_kernel.Ast

module Tag = struct
  type t = [
    | `Member
    | `Target
    | `Of
    | `From
    | `To
    | `Body
    | `Stmt
    | `Elem
    | `Storage
    | `Base
    | `Cond
    | `Name
    | `Type
    | `Branch
  ]

  let sexp_of_t (tag : t) =
    let open CCSexp in
    match tag with
    | `Member -> atom "Member"
    | `Target -> atom "Target"
    | `Of -> atom "Of"
    | `From -> atom "From"
    | `To -> atom "To"
    | `Body -> atom "Body"
    | `Stmt -> atom "Stmt"
    | `Elem -> atom "Elem"
    | `Storage -> atom "Storage"
    | `Base -> atom "Base"
    | `Cond -> atom "Cond"
    | `Name -> atom "Name"
    | `Type -> atom "Type"
    | `Branch -> atom "Branch"
end

module Form = struct
  type t = [
    | `Identifier of string
    | `Boolean of bool
    | `Numeric of string
    | `String of string
    | `A_list | `P_list
    | `Refer | `Deref
    | `Log_not | `Log_and | `Log_or
    | `Bit_not | `Bit_and | `Bit_or | `Bit_xor
    | `Shl | `Shr
    | `Negate | `Add | `Sub | `Mul | `Div
    | `Cmp_eq | `Cmp_ne | `Cmp_le | `Cmp_ge | `Cmp_lt | `Cmp_gt
    | `Member_access
    | `Subscript
    | `Call
    | `Array
    | `Range
    | `Iterable
    | `Block
    | `Stmt_use | `Stmt_constant | `Stmt_let | `Stmt_while | `Stmt_for
    | `Stmt_isr | `Stmt_assign | `Stmt_fun | `Stmt_expr | `Stmt_return
    | `Stmt_if | `Branch_if | `Branch_else
    | `Unit
    | `Type_primitive | `Type_ref | `Type_slice | `Type_array | `Type_fun
    | `Storage_default | `Storage_mut | `Storage_stash
  ]

  let sexp_of_t (form : t) =
    let open CCSexp in
    match form with
    | `Identifier id -> of_variant "Identifier" [atom id]
    | `Boolean b -> of_variant "Boolean" [of_bool b]
    | `Numeric n -> of_variant "Numeric" [atom n]
    | `String s -> of_variant "String" [atom s]
    | `A_list -> atom "A_list"
    | `P_list -> atom "P_list"
    | `Refer -> atom "Refer"
    | `Deref -> atom "Deref"
    | `Log_not -> atom "Log_not"
    | `Log_and -> atom "Log_and"
    | `Log_or -> atom "Log_or"
    | `Bit_not -> atom "Bit_not"
    | `Bit_and -> atom "Bit_and"
    | `Bit_or -> atom "Bit_or"
    | `Bit_xor -> atom "Bit_xor"
    | `Shl -> atom "Shl"
    | `Shr -> atom "Shr"
    | `Negate -> atom "Negate"
    | `Add -> atom "Add"
    | `Sub -> atom "Sub"
    | `Mul -> atom "Mul"
    | `Div -> atom "Div"
    | `Cmp_eq -> atom "Cmp_eq"
    | `Cmp_ne -> atom "Cmp_ne"
    | `Cmp_le -> atom "Cmp_le"
    | `Cmp_ge -> atom "Cmp_ge"
    | `Cmp_lt -> atom "Cmp_lt"
    | `Cmp_gt -> atom "Cmp_gt"
    | `Member_access -> atom "Member_access"
    | `Subscript -> atom "Subscript"
    | `Call -> atom "Call"
    | `Array -> atom "Array"
    | `Range -> atom "Range"
    | `Iterable -> atom "Iterable"
    | `Block -> atom "Block"
    | `Stmt_use -> atom "Stmt_use"
    | `Stmt_constant -> atom "Stmt_constant"
    | `Stmt_let -> atom "Stmt_let"
    | `Stmt_while -> atom "Stmt_while"
    | `Stmt_for -> atom "Stmt_for"
    | `Stmt_isr -> atom "Stmt_isr"
    | `Stmt_assign -> atom "Stmt_assign"
    | `Stmt_fun -> atom "Stmt_fun"
    | `Stmt_expr -> atom "Stmt_expr"
    | `Stmt_return -> atom "Stmt_return"
    | `Stmt_if -> atom "Stmt_if"
    | `Branch_if -> atom "Branch_if"
    | `Branch_else -> atom "Branch_else"
    | `Unit -> atom "Unit"
    | `Type_primitive -> atom "Type_primitive"
    | `Type_ref -> atom "Type_ref"
    | `Type_slice -> atom "Type_slice"
    | `Type_array -> atom "Type_array"
    | `Type_fun -> atom "Type_fun"
    | `Storage_default -> atom "Storage_default"
    | `Storage_mut -> atom "Storage_mut"
    | `Storage_stash -> atom "Storage_stash"
end

type syntax_node = (Form.t, Tag.t) Node.t

let identifier ?span id =
  Node.create (`Identifier id) ?span

let block ?span statements =
  let children = List.map (fun s -> (`Stmt, s)) statements in
  Node.create `Block ~children ?span

let op_prefix ?span form right =
  Node.create form ~children:[`Of, right] ?span

let op_binary ?span form left right =
  Node.create form ~children:[`Of, left; `Of, right] ?span
