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

type 'p error = ('p option * string) list lazy_t

type ('a, 'p) t = ('a, 'p error) result

let return = Result.return

let fail = Result.fail

let of_thunk f =
  Lazy.from_fun (fun () ->
      f ()
      |> List.map (fun msg -> (None, msg)))
  |> Result.fail

let of_lit loc_msgs =
  Lazy.from_val loc_msgs |> Result.fail

let of_lit_thunk f =
  Lazy.from_fun f |> Result.fail

let of_strings msgs =
  Lazy.from_fun (fun () -> List.map (fun msg -> (None, msg)) msgs)
  |> Result.fail

let of_thunks fs =
  Lazy.from_fun (fun () ->
      List.map (fun f -> (None, f ())) fs)
  |> Result.fail

let of_string msg =
  Lazy.from_val [None, msg]
  |> Result.fail

let of_option msg =
  Option.to_result (Lazy.from_val [None, msg])

let of_thunk1 f =
  Lazy.from_fun (fun () -> [None, f ()])
  |> Result.fail

let of_fmt format =
  Printf.ksprintf of_string format

let with_loc loc =
  let open Option.Infix in
  Result.map_err (fun err ->
      Lazy.from_fun (fun () ->
          Lazy.force err
          |> List.map (fun (ll, msg) -> (ll <+> loc, msg))))

let get = Lazy.force

let choose rs =
  let rec choose_aux errs = function
    | (Error e) :: tl -> choose_aux (e :: errs) tl
    | (Ok _) as ok :: _ -> ok
    | [] -> of_lit_thunk (fun () ->
        List.rev errs
        |> List.flat_map Lazy.force)
  in
  choose_aux [] rs

let all_ok lst =
  let rec aux_err acc = function
    | (Error err) :: tl -> aux_err (err :: acc) tl
    | (Ok _) :: tl -> aux_err acc tl
    | [] -> of_lit_thunk (fun () ->
        List.rev acc
        |> List.flat_map Lazy.force)
  in
  let rec aux_ok acc = function
    | (Error err) :: tl -> aux_err [err] tl
    | (Ok ok) :: tl -> aux_ok (ok :: acc) tl
    | [] -> List.rev acc |> Result.return
  in
  aux_ok [] lst

let map_err f = function
  | Ok _ as ok -> ok
  | Error err -> of_lit_thunk (fun () ->
      Lazy.force err
      |> List.map f)

let iter_err f = function
  | Ok _ -> ()
  | Error err -> Lazy.force err |> List.iter f

let pp pp_loc formatter =
  iter_err begin function
    | (Some loc, msg) -> Format.fprintf formatter "%a: @[%s@." pp_loc loc msg
    | (None, msg) -> Format.fprintf formatter "@[%s@." msg
  end
