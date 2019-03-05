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

type syntax_error = Lexer.syntax_error

open Stdio
open Jeff65_kernel

let print_position outc lexbuf =
  let (ps, pe) = Sedlexing.lexing_positions lexbuf in
  Out_channel.fprintf outc "%d:%d-%d:%d" ps.pos_lnum ps.pos_bol pe.pos_lnum pe.pos_bol

let parse_with_error lexbuf =
  let module I = Parser.MenhirInterpreter in
  let rec loop errors checkpoint =
    match checkpoint with
    | I.Accepted ast -> Ok ast

    | I.Rejected -> Error (List.rev errors)

    | I.HandlingError env ->
      let loc = Sedlexing.lexing_positions lexbuf in
      let errors = Lexer.Parse_error (env, loc) :: errors in
      I.resume checkpoint
      |> loop errors

    | I.Shifting (_, _, _)
    | I.AboutToReduce (_, _) ->
      I.resume checkpoint
      |> loop errors

    | I.InputNeeded _ ->
      match Lexer.read lexbuf with
      | Ok token -> I.offer checkpoint token
                    |> loop errors
      | Error err -> Error [err]
  in
  let (start, _) = Sedlexing.lexing_positions lexbuf in
  Parser.Incremental.unit start
  |> loop []

let sexp_of_syntax =
  Ast.Node.sexp_of_t Syntax.Form.sexp_of_t Syntax.Tag.sexp_of_t
