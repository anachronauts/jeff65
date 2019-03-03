(* jeff65 command-line driver
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
open Cmdliner

type copts = { debugopts : string list }

let help_secs = [
  `S Manpage.s_common_options;
  `P "These options are common to all commands.";
  `S "MORE HELP";
  `P "Use `$(mname) $(i,COMMAND) --help' for help on a single command.";
]

let copts debugopts = { debugopts }
let copts_t =
  let docs = Manpage.s_common_options in
  let debugopts =
    let doc = "Enable compiler debugging options." in
    Arg.(value & opt_all string [] & info ["Z"] ~docs ~doc)
  in
  Term.(const copts $ debugopts)

let compile copts =
  List.iter copts.debugopts ~f:(fun opt ->
    Stdio.print_endline opt);
  Stdio.print_endline "Compile"
let compile_cmd =
  Term.(const compile $ copts_t),
  Term.info "compile"

let default_cmd =
  let sdocs = Manpage.s_common_options in
  let man = help_secs in
  Term.(ret (const (fun _ -> `Help (`Pager, None)) $ copts_t)),
  Term.info "jeff65" ~sdocs ~man

let () = Term.exit @@ Term.eval_choice default_cmd [compile_cmd]

