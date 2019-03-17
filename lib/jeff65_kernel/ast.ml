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

open! Containers
open! Astring

type position = Lexing.position

let sexp_of_position pos =
  let { Lexing.pos_fname; pos_lnum; pos_bol; pos_cnum } = pos in
  CCSexp.(of_quad ( (atom pos_fname)
                  , (of_int pos_lnum)
                  , (of_int pos_bol)
                  , (of_int pos_cnum)
                  )
         )

type span = position * position

let sexp_of_span (pos1, pos2) =
  CCSexp.of_pair ( sexp_of_position pos1
                 , sexp_of_position pos2
                 )

module Node = struct
  type ('a, 'b) t = { form : 'a
                    ; span : span option
                    ; children : ('b * ('a, 'b) t) list
                    }

  let rec sexp_of_t sexp_of_a sexp_of_b node =
    let fields = match node.children with
      | [] -> []
      | cs ->
        let children = List.map
            (fun (b, n) ->
               CCSexp.of_pair (sexp_of_b b, sexp_of_t sexp_of_a sexp_of_b n))
            cs
        in
        [("children", CCSexp.of_list children)]
    in
    let fields = match node.span with
      | None -> fields
      | Some value -> ("span", sexp_of_span value) :: fields
    in
    let fields = ("form", sexp_of_a node.form) :: fields in
    CCSexp.of_record fields

  let create ?span ?(children = []) form =
    { form; span; children }
end
