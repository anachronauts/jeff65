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

type error

type 'a t = ('a, error) result

val return : 'a -> 'a t

val fail : error -> 'a t

val of_thunk : (unit -> string list) -> 'a t

val of_strings : string list -> 'a t

val of_thunks : (unit -> string) list -> 'a t

val of_string : string -> 'a t

val of_thunk1 : (unit -> string) -> 'a t

val of_fmt : ('a, unit, string, 'b t) format4 -> 'a

val to_strings : error -> string list

val choose : 'a t list -> 'a t

val map_err : (string -> string) -> 'a t -> 'a t

val iter_err : (string -> unit) -> 'a t -> unit

val to_channel : out_channel -> 'a t -> unit
