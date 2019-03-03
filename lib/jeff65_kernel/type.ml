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
open Base

type t =
  | Phantom
  | Void
  | Int of { width: int; signed: bool }
  | Ref of { target: t }
  | Function of { ret: t; args: t list }

let rec to_string =
  let open Printf in function
    | Phantom -> "???"
    | Void -> "void"
    | Int { width; signed } -> sprintf "%c%d" (if signed then 'i' else 'u') (width * 8)
    | Ref { target } -> sprintf "&%s" (to_string target)
    | Function { ret; args } ->
      let r = match ret with
        | Void -> ""
        | _ -> sprintf " -> %s" (to_string ret)
      in
      let a =
        List.map args ~f:to_string
        |> String.concat ~sep:", "
      in
      sprintf "fun(%s)%s" a r

(* TODO support other types *)
let can_assign ~lhs ~rhs =
  match (lhs, rhs) with
  | (Phantom, _) -> true
  | (_, Phantom) -> true
  | (Int { width = lwidth; signed = lsigned },
     Int { width = rwidth; signed = rsigned })
    when (Bool.equal lsigned rsigned) && lwidth >= rwidth -> true
  | _ -> false


let u8 = Int { width = 1; signed = false }
let u16 = Int { width = 2; signed = false }
let u24 = Int { width = 3; signed = false }
let u32 = Int { width = 4; signed = false }
let i8 = Int { width = 1; signed = true }
let i16 = Int { width = 2; signed = true }
let i24 = Int { width = 3; signed = true }
let i32 = Int { width = 4; signed = true }
let ref t = Ref { target = t }
let ptr = ref Phantom

