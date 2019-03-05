(* jeff65 AST manipulation
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
