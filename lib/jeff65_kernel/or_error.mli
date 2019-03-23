(* jeff65 error type
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

type 'p error

type ('a, 'p) t = ('a, 'p error) result

val return : 'a -> ('a, 'p) t

val fail : 'p error -> ('a, 'p) t

val of_thunk : (unit -> string list) -> ('a, 'p) t

val of_lit : ('p option * string) list -> ('a, 'p) t

val of_lit_thunk : (unit -> ('p option * string) list) -> ('a, 'p) t

val of_strings : string list -> ('a, 'p) t

val of_thunks : (unit -> string) list -> ('a, 'p) t

val of_string : string -> ('a, 'p) t

val of_option : string -> 'a option -> ('a, 'p) t

val of_thunk1 : (unit -> string) -> ('a, 'p) t

val of_fmt : ('a, unit, string, ('b, 'p) t) format4 -> 'a

val with_loc : 'p option -> ('a, 'p) t -> ('a, 'p) t

val get : 'p error -> ('p option * string) list

val choose : ('a, 'p) t list -> ('a, 'p) t

val all_ok : ('a, 'p) t list -> ('a list, 'p) t

val map_err :
  ('p option * string -> 'q option * string) ->
  ('a, 'p) t ->
  ('a, 'q) t

val iter_err : ('p option * string -> unit) -> ('a, 'p) t -> unit

val pp : 'p Fmt.t -> ('a, 'p) t Fmt.t
