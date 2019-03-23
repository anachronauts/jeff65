(* jeff65 AST manipulation
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

type position = Lexing.position

let sexp_of_position pos =
  let { Lexing.pos_fname; pos_lnum; pos_bol; pos_cnum } = pos in
  CCSexp.(of_quad ( (atom pos_fname)
                  , (of_int pos_lnum)
                  , (of_int pos_bol)
                  , (of_int pos_cnum)
                  )
         )

type span = position * position

type 'a or_error = ('a, span) Or_error.t

let sexp_of_span (pos1, pos2) =
  CCSexp.of_pair ( sexp_of_position pos1
                 , sexp_of_position pos2
                 )

let span_pp formatter loc =
  let ({ Lexing.pos_fname; pos_lnum; pos_cnum; pos_bol }, _) = loc in
  Format.fprintf formatter "%s:%d:%d" pos_fname pos_lnum (pos_cnum - pos_bol)

module Node = struct
  type ('f, 'k) t = { form : 'f
                    ; span : span option
                    ; children : ('k * ('f, 'k) t) list
                    }

  let create ?span ?(children = []) form =
    { form; span; children }

  let rec strip_spans ({ children; _ } as ast) =
    { ast with span = None
             ; children = List.map (fun (t, n) -> (t, strip_spans n)) children }

  let rec select sel nodes =
    let rec sel_one vs key = function
      | (k, v) :: tl when Equal.poly key k -> sel_one (v :: vs) key tl
      | _ :: tl -> sel_one vs key tl
      | [] -> vs
    in
    match sel with
    | hd :: tl -> List.flat_map (fun n -> sel_one [] hd n.children) nodes
                  |> select tl
    | [] -> nodes

  let select1 sel node =
    select sel [node]

  let patch_loc left right =
    match (left.span, right.span) with
    | (_, Some _) | (None, _) -> right
    | (Some _ as span, None) -> { right with span }

  let mapc f node =
    let f ((_, n) as kn) =
      let (k, r) = f kn in
      (k, patch_loc n r)
    in
    { node with children = List.map f node.children }

  let mapcf f node =
    let f ((_, n) as kn) =
      let open Result.Infix in
      f kn >|= (fun (k, r) -> (k, patch_loc n r))
    in
    List.map f node.children
    |> Or_error.all_ok
    |> Result.map (fun children -> { node with children })
    |> Or_error.with_loc node.span

  let rec walkx_post f node =
    List.map (fun (t, n) -> (t, walkx_post f n)) node.children
    |> f node.form node.span
    |> patch_loc node

  let rec walkxr_post f node =
    List.map (fun (t, n) -> (t, walkxr_post f n)) node.children
    |> f node.form node.span

  let rec walkxf_post f node =
    let open Result.Infix in
    List.map (fun (t, n) ->
        walkxf_post f n
        |> Result.map (fun n -> (t, n)))
      node.children
    |> Or_error.all_ok
    >>= f node.form node.span
    >|= patch_loc node
    |> Or_error.with_loc node.span

  let rec walkxrf_post f node =
    let open Result.Infix in
    List.map (fun (t, n) ->
        walkxrf_post f n
        |> Result.map (fun n -> (t, n)))
      node.children
    |> Or_error.all_ok
    >>= f node.form node.span
    |> Or_error.with_loc node.span

  let rec walkx_pre f node =
    f node.form node.span node.children
    |> mapc (fun (t, n) -> (t, walkx_pre f n))
    |> patch_loc node

  let rec walkxf_pre f node =
    let open Result.Infix in
    f node.form node.span node.children
    >>= mapcf (fun (t, n) ->
        walkxf_pre f n
        |> Result.map (fun n -> (t, n)))
    >|= patch_loc node
    |> Or_error.with_loc node.span

  let rec walk_post f node =
    mapc (fun (t, n) -> (t, walk_post f n)) node
    |> f |> patch_loc node

  let rec walkf_post f node =
    let open Result.Infix in
    mapcf (fun (t, n) ->
        walkf_post f n
        |> Result.map (fun n -> (t, n)))
      node
    >>= f
    >|= patch_loc node
    |> Or_error.with_loc node.span

  let rec walk_pre f node =
    f node |> mapc (fun (t, n) -> (t, walk_pre f n))
    |> patch_loc node

  let rec walkf_pre f node =
    let open Result.Infix in
    f node >>= mapcf (fun (t, n) ->
        walkf_pre f n
        |> Result.map (fun n -> (t, n)))
    >|= patch_loc node
    |> Or_error.with_loc node.span

  let rec mapt f node =
    List.map (fun (t, n) -> (t, mapt f n)) node.children
    |> f node
    |> patch_loc node

  let rec maptr f node =
    List.map (fun (t, n) -> (t, maptr f n)) node.children
    |> f node

  let rec maptf f node =
    let open Result.Infix in
    List.map (fun (t, n) ->
        maptf f n
        |> Result.map (fun n -> (t, n)))
      node.children
    |> Or_error.all_ok
    >>= f node
    >|= patch_loc node
    |> Or_error.with_loc node.span

  let rec maptrf f node =
    let open Result.Infix in
    List.map (fun (t, n) ->
        maptrf f n
        |> Result.map (fun n -> (t, n)))
      node.children
    |> Or_error.all_ok
    >>= f node
    |> Or_error.with_loc node.span

  let rec foldt_left f init tag node =
    List.fold_left (fun acc (t, n) -> foldt_left f acc t n)
      init node.children
    |> (fun acc -> f acc tag node)

  let rec foldtf_left f init tag node =
    let open Result.Infix in
    Result.fold_l
      (fun acc (t, n) -> foldtf_left f acc t n)
      init node.children
    >>= (fun acc -> f acc tag node)
    |> Or_error.with_loc node.span

  let rec foldt_right f tag node init =
    List.fold_right (fun (t, n) -> foldt_right f t n) node.children init
    |> f tag node

  let rec foldtf_right f tag node init =
    let open Result.Infix in
    List.fold_right (fun (t, n) acc ->
        acc >>= foldtf_right f t n)
      node.children (Ok init)
    >>= f tag node
    |> Or_error.with_loc node.span

  let sexp_of_t sexp_of_f sexp_of_k =
    let with_form f = List.cons ("form", sexp_of_f f) in
    let with_span s =
      Option.map (fun s -> ("span", sexp_of_span s)) s |> List.cons_maybe
    in
    let with_children cs =
      match
        List.map (fun (k, e) -> CCSexp.of_pair (sexp_of_k k, e)) cs
      with
      | [] -> Fun.id
      | cs -> List.cons ("children", CCSexp.of_list cs)
    in
    walkxr_post (fun f s c ->
        with_children c []
        |> with_span s
        |> with_form f
        |> CCSexp.of_record)
end
