open Jeff65_kernel

let parse source =
  Sedlexing.Utf8.from_string source
  |> Gold.parse_with_error
  |> Result.map Ast.Node.strip_spans

let ast_or_error =
  let pp formatter = function
    | Ok ast -> Gold.Syntax.pp formatter ast
    | Error _ as err -> Or_error.pp Ast.span_pp formatter err
  in
  let eq left right =
    match (left, right) with
    | (Ok _, Error _)
    | (Error _, Ok _) -> false
    | (Ok ll, Ok rr) -> CCSexp.equal
                          (Gold.Syntax.sexp_of_t ll)
                          (Gold.Syntax.sexp_of_t rr)
    | (Error _, Error _) -> failwith "can't compare errors yet"
  in
  Alcotest.testable pp eq

let empty_file () =
  Alcotest.(check ast_or_error)
    __LOC__
    (Ok (Ast.Node.create `Unit))
    (parse "")

let whitespace_only_file () =
  Alcotest.(check ast_or_error)
    __LOC__
    (Ok (Ast.Node.create `Unit))
    (parse "\n")

(* TODO Parse comments *)
(* let comments_newline () =
 *   Alcotest.(check ast)
 *     __LOC__
 *     (Ast.Node.create `Unit)
 *     (parse "--[[ a comment ]]\n" |> get_exn) *)

let precedence_add_mul () =
  Alcotest.(check ast_or_error)
    __LOC__
    (Ok Ast.Node.(
         create `Add ~children:
           [ `Of, create (`Numeric "1")
           ; `Of, create `Mul ~children:
               [ `Of, create (`Numeric "2")
               ; `Of, create (`Numeric "3")
               ]
           ]))
    (parse "constant x: u8 = 1 + 2 * 3"
     |> Result.map (Ast.Node.select1 [`Body; `Of])
     |> Result.map List.hd)

let syntax =
  [ "Empty file", `Quick, empty_file
  ; "Whitespace-only file", `Quick, whitespace_only_file
  (* ; "Comment w/ newline", `Quick, comments_newline *)
  ; "Precedence +, *", `Quick, precedence_add_mul
  ]
