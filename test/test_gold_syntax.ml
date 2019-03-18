open! Containers
open! Astring
open Jeff65_kernel

let parse source =
  Sedlexing.Utf8.from_string source
  |> Gold.parse_with_error
  |> Result.map Ast.Node.strip_spans

let get_exn result =
  let to_err = function
    | Error e -> e
    | _ -> assert false
  in
  match result with
  | Ok value -> value
  | Error errs -> List.map Gold.error_of_syntax_error errs
                  |> Or_error.choose
                  |> to_err
                  |> Or_error.to_strings
                  |> String.concat ~sep:"\n"
                  |> failwith

let ast =
  Alcotest.testable
    Gold.Syntax.pp
    (Fun.compose_binop Gold.Syntax.sexp_of_t CCSexp.equal)

let empty_file () =
  Alcotest.(check ast)
    __LOC__
    (Ast.Node.create `Unit)
    (parse "" |> get_exn)

let whitespace_only_file () =
  Alcotest.(check ast)
    __LOC__
    (Ast.Node.create `Unit)
    (parse "\n" |> get_exn)

(* TODO Parse comments *)
(* let comments_newline () =
 *   Alcotest.(check ast)
 *     __LOC__
 *     (Ast.Node.create `Unit)
 *     (parse "--[[ a comment ]]\n" |> get_exn) *)

let precedence_add_mul () =
  Alcotest.(check ast)
    __LOC__
    (Ast.Node.create `Add ~children:
       [ `Of, Ast.Node.create (`Numeric "1")
       ; `Of, Ast.Node.create `Mul ~children:
           [ `Of, Ast.Node.create (`Numeric "2")
           ; `Of, Ast.Node.create (`Numeric "3")
           ]
       ])
    (parse "constant x: u8 = 1 + 2 * 3"
     |> get_exn
     |> Ast.Node.select1 [`Body; `Of]
     |> List.hd)

let syntax =
  [ "Empty file", `Quick, empty_file
  ; "Whitespace-only file", `Quick, whitespace_only_file
  (* ; "Comment w/ newline", `Quick, comments_newline *)
  ; "Precedence +, *", `Quick, precedence_add_mul
  ]
