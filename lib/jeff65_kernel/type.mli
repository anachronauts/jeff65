(* jeff65 type system
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

type t =
  | Phantom
  | Void
  | Int of { width: int; signed: bool }
  | Ref of { target: t }
  | Function of { ret: t; args: t list }

val to_string : t -> string

(* TODO support other types *)
val can_assign : lhs:t -> rhs:t -> bool

val u8 : t
val u16 : t
val u24 : t
val u32 : t
val i8 : t
val i16 : t
val i24 : t
val i32 : t
val ref : t -> t
val ptr : t

