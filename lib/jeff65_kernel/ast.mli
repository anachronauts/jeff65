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

type 'a or_error = ('a, span) Or_error.t

val sexp_of_span : span -> CCSexp.t

val span_pp : span Fmt.t

module Node : sig
  type ('f, 'k) t = { form : 'f
                    ; span : span option
                    ; children : ('k * ('f, 'k) t) list
                    }

  val sexp_of_t : ('f -> CCSexp.t) -> ('k -> CCSexp.t) -> ('f, 'k) t -> CCSexp.t

  val create : ?span:span -> ?children:('k * ('f, 'k) t) list -> 'f -> ('f, 'k) t

  val strip_spans : ('f, 'k) t -> ('f, 'k) t

  val select : 'k list -> ('f, 'k) t list -> ('f, 'k) t list

  val select1 : 'k list -> ('f, 'k) t -> ('f, 'k) t list

  val mapc :
    ('k * ('f, 'k) t -> 'j * ('f, 'j) t) ->
    ('f, 'k) t ->
    ('f, 'j) t

  val mapcf :
    ('k * ('f, 'k) t -> ('j * ('f, 'j) t) or_error) ->
    ('f, 'k) t ->
    ('f, 'j) t or_error

  val walkx_post :
    ('f -> span option -> ('k * (('g, 'j) t as 'a)) list -> 'a) ->
    ('f, 'k) t ->
    'a

  val walkxr_post :
    ('f -> span option -> ('k * 'a) list -> 'a) ->
    ('f, 'k) t ->
    'a

  val walkxf_post :
    ('f -> span option -> ('k * (('g, 'j) t as 'a)) list -> 'a or_error) ->
    ('f, 'k) t ->
    'a or_error

  val walkxrf_post :
    ('f -> span option -> ('k * 'a) list -> 'a or_error) ->
    ('f, 'k) t ->
    'a or_error

  val walkx_pre :
    ('f -> span option -> ('k * ('f, 'k) t) list -> ('f, 'k) t) ->
    ('f, 'k) t ->
    ('f, 'k) t

  val walkxf_pre :
    ('f -> span option -> ('k * ('f, 'k) t) list -> ('f, 'k) t or_error) ->
    ('f, 'k) t ->
    ('f, 'k) t or_error

  val walk_post :
    (('f, 'k) t -> ('f, 'k) t) ->
    ('f, 'k) t ->
    ('f, 'k) t

  val walkf_post :
    (('f, 'k) t -> ('f, 'k) t or_error) ->
    ('f, 'k) t ->
    ('f, 'k) t or_error

  val walk_pre :
    (('f, 'k) t -> ('f, 'k) t) ->
    ('f, 'k) t ->
    ('f, 'k) t

  val walkf_pre :
    (('f, 'k) t -> ('f, 'k) t or_error) ->
    ('f, 'k) t ->
    ('f, 'k) t or_error

  val mapt :
    (('f, 'k) t -> ('k * (('g, 'j) t as 'a)) list -> 'a) ->
    ('f, 'k) t ->
    'a

  val maptr :
    (('f, 'k) t -> ('k * 'a) list -> 'a) ->
    ('f, 'k) t ->
    'a

  val maptf :
    (('f, 'k) t -> ('k * (('g, 'j) t as 'a)) list -> 'a or_error) ->
    ('f, 'k) t ->
    'a or_error

  val maptrf :
    (('f, 'k) t -> ('k * 'a) list -> 'a or_error) ->
    ('f, 'k) t ->
    'a or_error

  val foldt_left :
    ('a -> 'k -> ('f, 'k) t -> 'a) ->
    'a ->
    'k ->
    ('f, 'k) t ->
    'a

  val foldtf_left :
    ('a -> 'k -> ('f, 'k) t -> 'a or_error) ->
    'a ->
    'k ->
    ('f, 'k) t ->
    'a or_error

  val foldt_right :
    ('k -> ('f, 'k) t -> 'a -> 'a) ->
    'k ->
    ('f, 'k) t ->
    'a ->
    'a

  val foldtf_right :
    ('k -> ('f, 'k) t -> 'a -> 'a or_error) ->
    'k ->
    ('f, 'k) t ->
    'a ->
    'a or_error
end

