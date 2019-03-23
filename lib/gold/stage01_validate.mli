(* jeff65 gold-syntax validation passes
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

open Jeff65_kernel

module Form : sig
  type t = [
    | `Type_obj of Type.t
    | `Integer of int
  ]

  type xt = [t | Syntax.Form.t]

  val sexp_of_t : t -> CCSexp.t

  val sexp_of_xt : xt -> CCSexp.t
end

val run :
  (Syntax.Form.t, Syntax.Tag.t) Ast.Node.t ->
  (Form.xt, Syntax.Tag.t) Ast.Node.t Ast.or_error

val pp : ((Form.xt, Syntax.Tag.t) Ast.Node.t) Fmt.t
