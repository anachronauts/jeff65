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

open Jeff65_kernel

module Syntax = Syntax

module Debug_opts : sig
  type t = { log_debug : bool
           ; show_spans : bool
           }

  val t_of_string_list : string list -> t Or_error.t
end

module Compile_opts : sig
  type t = { in_path : Fpath.t
           ; out_path : Fpath.t
           ; debug_opts : Debug_opts.t
           }
end

val compile : Compile_opts.t -> unit Or_error.t

val parse_with_error : Sedlexing.lexbuf ->
  (Syntax.t, Lexer.syntax_error list) result

val error_of_syntax_error : Lexer.syntax_error -> 'a Or_error.t
