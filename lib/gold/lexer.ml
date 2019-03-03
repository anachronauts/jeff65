(* jeff65 gold-syntax lexer
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

open Sedlexing
open Parser

type token = Parser.token * Lexing.position * Lexing.position

type syntax_error =
  | Lex_error of string * Ast.span
  | Parse_error of Ast.Node.t MenhirInterpreter.env * Ast.span

let specials =
  [%sedlex.regexp? '(' | ')' | '[' | ']' | '{' | '}'
                 | ':' | ';' | '.' | ',' | '"' | '\\' | '@' | '&']

let tok_end = [%sedlex.regexp? white_space | specials]

let match_error buf =
  match%sedlex buf with
  | any, Star (Compl tok_end) ->
    let bad_text = Utf8.lexeme buf in
    let loc = lexing_positions buf in
    Lex_error (bad_text, loc)
  | _ -> assert false

let rec lex_main buf =
  match%sedlex buf with
  | white_space -> lex_main buf
  | "and" -> Ok OPERATOR_AND
  | "bitand" -> Ok OPERATOR_BITAND
  | "bitor" -> Ok OPERATOR_BITOR
  | "bitxor" -> Ok OPERATOR_BITXOR
  | "constant" -> Ok STMT_CONSTANT
  | "do" -> Ok PUNCT_DO
  | "else" -> Ok PUNCT_ELSE
  | "elseif" -> Ok PUNCT_ELSEIF
  | "end" -> Ok PUNCT_END
  | "endfun" -> Ok PUNCT_ENDFUN
  | "endisr" -> Ok PUNCT_ENDISR
  | "for" -> Ok STMT_FOR
  | "fun" -> Ok STMT_FUN
  | "if" -> Ok STMT_IF
  | "in" -> Ok PUNCT_IN
  | "isr" -> Ok STMT_ISR
  | "let" -> Ok STMT_LET
  | "mut" -> Ok STORAGE_MUT
  | "not" -> Ok OPERATOR_NOT
  | "or" -> Ok OPERATOR_OR
  | "return" -> Ok STMT_RETURN
  | "stash" -> Ok STORAGE_STASH
  | "then" -> Ok PUNCT_THEN
  | "to" -> Ok PUNCT_TO
  | "use" -> Ok STMT_USE
  | "while" -> Ok STMT_WHILE
  | ('0' .. '9'), Star (Compl tok_end) -> Ok (NUMERIC (Utf8.lexeme buf))
  | xid_start, Star(Compl tok_end) -> Ok (IDENTIFIER (Utf8.lexeme buf))
  (* TODO comments *)
  (* TODO strings *)
  | "==" -> Ok OPERATOR_EQ
  | "<>" -> Ok OPERATOR_NE
  | "!=" -> Ok OPERATOR_NE
  | "<=" -> Ok OPERATOR_LE
  | ">=" -> Ok OPERATOR_GE
  | "<" -> Ok OPERATOR_LT
  | ">" -> Ok OPERATOR_GT
  | "=" -> Ok OPERATOR_ASSIGN
  | "+=" -> Ok OPERATOR_ASSIGN_INC
  | "-=" -> Ok OPERATOR_ASSIGN_DEC
  | "+" -> Ok OPERATOR_PLUS
  | "-" -> Ok OPERATOR_MINUS
  | "*" -> Ok OPERATOR_TIMES
  | "/" -> Ok OPERATOR_DIVIDE
  | "<<" -> Ok OPERATOR_SHL
  | ">>" -> Ok OPERATOR_SHR
  | "." -> Ok OPERATOR_DOT
  | "@" -> Ok OPERATOR_DEREF
  | "&" -> Ok OPERATOR_REF
  | "->" -> Ok PUNCT_ARROWR
  | ":" -> Ok PUNCT_COLON
  | "," -> Ok PUNCT_COMMA
  | ";" -> Ok PUNCT_SEMICOLON
  | "(" -> Ok PAREN_OPEN
  | ")" -> Ok PAREN_CLOSE
  | "[" -> Ok BRACKET_OPEN
  | "]" -> Ok BRACKET_CLOSE
  | eof -> Ok EOF
  | _ -> Error (match_error buf)

let read lexbuf =
  match lex_main lexbuf with
  | Ok token ->
    let (ts, te) = lexing_positions lexbuf in
    Ok (token, ts, te)

  | Error _ as e -> e
