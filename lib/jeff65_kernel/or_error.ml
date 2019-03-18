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

open! Containers
open! Astring

type error = string list lazy_t

type 'a t = ('a, error) result

let return = Result.return

let fail = Result.fail

let of_thunk f =
  Lazy.from_fun f |> fail

let of_strings msgs =
  Lazy.from_val msgs |> fail

let of_thunks fs =
  Lazy.from_fun (fun () ->
      List.map (Fun.(|>) ()) fs)
  |> Result.fail

let of_string msg =
  Lazy.from_val [msg]
  |> Result.fail

let of_thunk1 f =
  Lazy.from_fun (fun () -> [f ()])
  |> Result.fail

let of_fmt format =
  Printf.ksprintf of_string format

let to_strings = Lazy.force

let choose rs =
  let rec err_collect_aux errs = function
    | (Error e) :: tl -> err_collect_aux (e :: errs) tl
    | (Ok _) as ok :: _ -> ok
    | [] -> of_thunk (fun () ->
        List.rev errs
        |> List.flat_map Lazy.force)
  in
  err_collect_aux [] rs

let map_err f = function
  | Ok _ as ok -> ok
  | Error err -> of_thunk (fun () ->
      Lazy.force err
      |> List.map f)

let iter_err f = function
  | Ok _ -> ()
  | Error err -> Lazy.force err |> List.iter f

let to_channel channel =
  iter_err (Printf.fprintf channel "%s\n")
