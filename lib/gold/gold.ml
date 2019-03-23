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

open! Containers
open! Astring
open Jeff65_kernel

module Syntax = Syntax

module Debug_opts = struct
  type t = { log_debug : bool
           ; show_spans : bool
           }

  module S = Set.Make(String)

  let all_opts = S.of_list ["log_debug"; "show_spans"]

  let fmt_opts () = String.concat ~sep:" "

  let t_of_string_list opts =
    let opts = S.of_list opts in
    match S.diff opts all_opts |> S.to_list with
    | [] -> Ok { log_debug = S.mem "log_debug" opts
               ; show_spans = S.mem "show_spans" opts
               }
    | _ as bad ->
      Or_error.of_fmt
        "No debug options matching any of: %a. Available options are: %a."
        fmt_opts bad fmt_opts (S.to_list all_opts)
end

module Compile_opts = struct
  type t = { in_path : Fpath.t
           ; out_path : Fpath.t
           ; debug_opts : Debug_opts.t
           }
end

let error_of_syntax_error = function
  | Lexer.Lex_error (msg, loc) -> Or_error.of_string msg
                                  |> Or_error.with_loc (Some loc)
  (* TODO real messages *)
  | Lexer.Parse_error (_, loc) -> Or_error.of_string "syntax error"
                                  |> Or_error.with_loc (Some loc)

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
  |> function
  | Ok _ as ok -> ok
  | Error errs -> List.map error_of_syntax_error errs |> Or_error.choose

let compile opts =
  let open Result.Infix in
  let in_path = Fpath.to_string opts.Compile_opts.in_path in
  IO.with_in in_path (fun in_file ->
      let lexbuf = Sedlexing.Utf8.from_channel in_file in
      Sedlexing.set_filename lexbuf in_path;
      parse_with_error lexbuf
      >>= Stage01_validate.run
      >|= (fun ast -> if opts.debug_opts.show_spans then ast else Ast.Node.strip_spans ast)
      >|= Stage01_validate.pp Format.stdout
      (* >|= Syntax.pp Format.stdout *)
      >|= print_newline)
