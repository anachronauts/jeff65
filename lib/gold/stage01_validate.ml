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

module Form = struct
  type t = [
    | `Type_obj of Type.t
    | `Integer of int
  ]

  type xt = [t | Syntax.Form.t]

  let sexp_of_t (form : t) =
    match form with
    | `Type_obj ty -> CCSexp.(of_variant "Type_obj" [Type.to_string ty |> atom])
    | `Integer n -> CCSexp.(of_variant "Integer" [of_int n])

  let sexp_of_xt = function
    | #t as form -> sexp_of_t form
    | #Syntax.Form.t as form -> Syntax.Form.sexp_of_t form
end

let expand node =
  (node : (Syntax.Form.t, Syntax.Tag.t) Ast.Node.t :> (Form.xt, Syntax.Tag.t) Ast.Node.t)

let expect_identifier node =
  match node.Ast.Node.form with
  | `Identifier id -> Ok id
  | _ -> Or_error.of_string "Expected identifier"

let expect_type_obj node =
  match node.Ast.Node.form with
  | `Type_obj obj -> Ok obj
  | _ -> Or_error.of_string "Expected type object"

let type_of_name = function
  | "void" -> Ok Type.Void
  | "u8" -> Ok Type.u8
  | "u16" -> Ok Type.u16
  | "u24" -> Ok Type.u24
  | "u32" -> Ok Type.u32
  | "i8" -> Ok Type.i8
  | "i16" -> Ok Type.i16
  | "i24" -> Ok Type.i24
  | "i32" -> Ok Type.i32
  | t -> Or_error.of_fmt "Unknown type name '%s'" t

let parse_numbers ast =
  let aux node =
    match node.Ast.Node.form with
    | `Numeric num ->
      Int.of_string num
      |> Or_error.of_option ("Invalid number " ^ num)
      |> Result.map (fun n -> Ast.Node.create (`Integer n))
    | _ -> Ok node
  in
  Ast.Node.walkf_post aux ast

let construct_types ast =
  let aux node =
    let open Result.Infix in
    match node.Ast.Node.form with
    | `Type_primitive ->
      Ast.Node.select1 [`Name] node |> List.head_opt
      |> Or_error.of_option "Missing name"
      >>= expect_identifier
      >>= type_of_name
      >|= (fun t -> Ast.Node.create (`Type_obj t))
    | `Type_ref ->
      (* TODO handle storage *)
      Ast.Node.select1 [`Base] node |> List.head_opt
      |> Or_error.of_option "Missing base"
      >>= expect_type_obj
      >|= Type.ref
      >|= (fun t -> Ast.Node.create (`Type_obj t))
    | `Type_fun ->
      (* TODO handle arguments *)
      Ast.Node.select1 [`To] node |> List.head_opt
      |> Or_error.of_option "Missing tag To"
      >>= expect_type_obj
      >|= (fun ret -> Type.Function { ret; args = [] })
      >|= (fun t -> Ast.Node.create (`Type_obj t))
    | _ -> Ok node
  in
  Ast.Node.walkf_post aux ast

let run ast =
  let open Result.Infix in
  Ok (expand ast)
  >>= parse_numbers
  >>= construct_types

let pp formatter ast =
  Ast.Node.sexp_of_t Form.sexp_of_xt Syntax.Tag.sexp_of_t ast
  |> CCSexp.pp formatter
