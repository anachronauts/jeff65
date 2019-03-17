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

type position = Lexing.position
val sexp_of_position : position -> CCSexp.t

type span = position * position

val sexp_of_span : span -> CCSexp.t

module Node : sig
  type ('a, 'b) t = { form : 'a
                    ; span : span option
                    ; children : ('b * ('a, 'b) t) list
                    }

  val sexp_of_t : ('a -> CCSexp.t) -> ('b -> CCSexp.t) -> ('a, 'b) t -> CCSexp.t

  val create : ?span:span -> ?children:('b * ('a, 'b) t) list -> 'a -> ('a, 'b) t
end
