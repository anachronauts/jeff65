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

open Base
open Sexplib.Conv
open Sexplib.Std

type position = Lexing.position

let position_of_sexp exp =
  let (pos_fname, pos_lnum, pos_bol, pos_cnum) =
    [%of_sexp: string * int * int * int] exp
  in
  { Lexing.pos_fname; pos_lnum; pos_bol; pos_cnum }

let sexp_of_position pos =
  let { Lexing.pos_fname; pos_lnum; pos_bol; pos_cnum } = pos in
  [%sexp_of: string * int * int * int] (pos_fname, pos_lnum, pos_bol, pos_cnum)

type span = position * position
[@@deriving sexp]

module Node = struct
  type ('a, 'b) t = { form : 'a
                    ; span : span sexp_option
                    ; children : ('b * ('a, 'b) t) sexp_list
                    }
  [@@deriving fields, sexp]

  let create ?span ?(children = []) form =
    { form; span; children }
end

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
  [@@deriving variants, sexp]
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
  [@@deriving variants, sexp]
end

let identifier ?span id =
  Node.create (`Identifier id) ?span

let block ?span statements =
  let children = List.map statements ~f:(fun s -> (`Stmt, s)) in
  Node.create `Block ~children ?span

let op_prefix ?span form right =
  Node.create form ~children:[`Of, right] ?span

let op_binary ?span form left right =
  Node.create form ~children:[`Of, left; `Of, right] ?span
