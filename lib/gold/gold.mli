(* jeff65 gold-syntax
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

module Ast = Ast

type syntax_error = Lexer.syntax_error

val print_position : Stdio.Out_channel.t -> Sedlexing.lexbuf -> unit

val parse_with_error :
  Sedlexing.lexbuf
  -> ((Ast.Form.t, Ast.Tag.t) Ast.Node.t, syntax_error list) result
