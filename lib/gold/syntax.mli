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

open Jeff65_kernel.Ast

module Tag : sig
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

  val sexp_of_t : t -> CCSexp.t
end

module Form : sig
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

  val sexp_of_t : t -> CCSexp.t
end

val sexp_of_t : (Form.t, Tag.t) Node.t -> CCSexp.t

val identifier : ?span:span -> string -> ([> `Identifier of string], 'b) Node.t

val block :
  ?span:span
  -> ([> `Block] as 'a, [> `Stmt] as 'b) Node.t list
  -> ('a, 'b) Node.t

val op_prefix :
  ?span:span
  -> 'a
  -> ('a, [> `Of] as 'b) Node.t
  -> ('a, 'b) Node.t

val op_binary :
  ?span:span
  -> 'a
  -> ('a, [> `Of] as 'b) Node.t
  -> ('a, 'b) Node.t
  -> ('a, 'b) Node.t

val pp : (Form.t, Tag.t) Node.t Fmt.t
