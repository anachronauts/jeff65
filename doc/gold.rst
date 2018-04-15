===========================
 Gold-syntax Specification
===========================

This document defines the syntax and semantics of gold-syntax units for the
jeff65 compiler.

To propose a change to this document, create a pull request from a branch with a
name beginning with ``spec-gold-``, which contains the edits to this document
relevant to enact the change, and if possible, the necessary alterations to the
parser and/or lexer. (If those changes would be high-effort, open a bug once the
PR has been accepted.)

.. contents::


Syntax
======

Gold-syntax files consist of printable ASCII characters, which are divided into
the following groups:

- whitespace, any of SPACE, TAB, LINE FEED, or CARRIAGE RETURN

- special delimiters, any of ``( ) [ ] { } : ; . , " \ @ &``

- alphanumeric characters, any of ``A-Za-z0-9``. Note that the underscore is not
  included (though it is allowed in identifiers, but discouraged).

- punctuation, any of ``! $ % ' * + - / < = > ? ^ _ ` | ~`` (i.e. the remaining
  ASCII characters).

Gold-syntax tokens are delimited by whitespace, which is discarded, and the
special delimiters, which are considered single tokens. Note that new line
characters are not treated specially. Also note that comments are treated
specially by the parser; see below.

A token beginning with a digit in ``0-9`` is assumed to be a numeric value. A
valid numeric value must be one of the following:

1. A sequence of characters in ``0-9``, such as ``1``, ``42``, or ``094``,
   denotes a decimal (base-10) integer. Note that numbers beginning with a ``0``
   are considered to be decimal, not octal.

2. The characters ``0x`` or ``0X`` (a digit zero followed by an uppercase or
   lowercase letter 'X') followed by a sequence of characters in ``0-9A-Fa-f``,
   such as ``0x1``, ``0xa9``, or ``0xbeef``, denotes a hexadecimal (base-16)
   integer.

3. The characters ``0o`` or ``0O`` (a digit zero followed by an uppercase or
   lowercase letter 'O') followed by a sequence of characters in ``0-7``, such
   as ``0o644``, denotes an octal (base-8) integer. Note that numbers beginning
   with a ``0`` (zero) followed by digits are considered to be decimal, not
   octal.

4. The characters ``0b`` or ``0B`` (a digit zero followed by an uppercase or
   lowercase letter 'B') followed by a sequence of characters in ``0 1``, such
   as ``0b11010001``, denotes a binary (base-2) integer.

A token beginning with a digit in ``0-9`` and not conforming to one of the above
rules is an error.

A token beginning with a letter in ``A-Za-z`` is assumed to be an identifier.
The restriction to a letter applies only to the first character; identifiers may
contain any printable ASCII character which does not delimit a token. For
example, ``foo-bar?`` is considered a valid identifier.

A token beginning with a punctuation character continues until the first
non-punctuation character, at which point it will end, regardless of whether a
whitespace character, comment, or special delimiter has been encountered.
Therefore ``-1`` becomes two tokens.

.. attention:: The above rules imply that the string ``1+2`` is considered a
               single, invalid, numeric token, and the string ``x-2`` is
               considered an identifier. Make sure to put spaces around your
               operators!


Language Elements
=================

A Gold-syntax unit consists of a series of top-level statements.

Binding Statements
------------------

The following statements introduce bindings of names. They are all allowed at
the top level of the file, and a subset are allowed inside executable code
blocks.

Top-level bindings are visible throughout the program. Block-level bindings are
visible until the end of the scope in which they are introduced. Introducing a
block-level binding with the same name as another binding, even in the same
scope, will result in the previous binding being shadowed until the new binding
goes out of scope, at which time the previous binding will be restored.

It is an error to introduce a new top-level binding with the same name as
another top-level binding.


``use``
~~~~~~~

Top-level usage: ::

  use <identifier>

Locates a unit named with the given identifier, and makes its exported symbols
available in the current unit in a namespace bound to the same name as the unit.
If the unit cannot be located, a compilation error will be raised.

The binding introduced by a ``use`` statement is not exported from the unit.

Units have names derived from the name of the file they are defined in, and thus
the allowed names for units may be further restricted by what characters are
allowed in filenames on your system. For maximum portability, stick to
alphanumeric characters and the character ``-`` (hyphen minus) in your unit
names.


``constant``
~~~~~~~~~~~~

Top-level / block-level usage: ::

  constant <identifier> : <type> = <known-expression>

Binds a name to a value known at compile time which does not allocate memory in
the program image. The value will be inlined at usage sites. Top-level constant
bindings are exported from the unit as symbols, and may be referenced in other
units.

The restriction to values which do not allocate memory means that arrays and
strings cannot be declared as constant-bindings. It is possible to declare
pointers and slices as constants through the use of certain functions exported
from the built-in ``mem`` unit.


``let``
~~~~~~~

Top-level usage ::

  let [mut] <identifier> : <type> = <known-expression>

Binds a name to a value known at compile time. Always allocates memory in the
program image. Top-level let-bindings are exported from the unit as symbols
which may be referenced in other units.

Block-level usage: ::

  let [mut] <identifier> : <type> = <expression>
  let stash <identifier> : <type> = <known-expression>

Binds a name to a value. In the first form, memory is allocated statically (i.e.
memory is reserved, but the value is not included in the program image), and the
value is computed and stored when the statement is executed. In the second form,
memory is allocated in the program image with the initial value stored.

By default, let-bindings are immutable, thought they may be shadowed by
re-binding. If the ``mut`` or ``stash`` storage classes are applied, then the
binding becomes mutable, and the value may be changed.


``fun``
~~~~~~~

Top-level usage: ::

  fun <identifier>([<identifier> : <type> [, ...]]) [-> <type-expression>]
    [...]
  endfun

Binds a name to a function with zero or more arguments and an optional return
type. Introduces a new scope, and statements inside are considered block-level
statements.

A function with a return type must terminate by executing a ``return``
statement.

Note that the type of the binding introduced is a function type. Function types
may only be used to call the function or get a pointer to its address using the
``&`` operator.


``isr``
~~~~~~~

Top-level usage: ::

  isr <identifier>
    [...]
  endisr 

Binds a name to an interrupt service routine. Introduces a new scope, and
statements inside are considered block-level statements.

Note that the type of the binding introduced is an ISR type. ISR types may only
be used to get a pointer to its address using the ``&`` operator.


Control Flow Statements
-----------------------

Control flow statements may only be used in block-level contexts. Additional
restrictions may apply to individual statements, depending on context.
Gold-syntax programs are executed statement-by-statement unless a control-flow
statement is encountered.


``return``
~~~~~~~~~~

Usage: ::

  return [<expression>]

Terminates execution of the current function, returning control to the caller,
and possibly returning a value. This will cause any currently-executing loops to
terminate.

If the current function does not have a return type, then the expression is
disallowed; if the current function does have a return type, then the expression
is required, and must have a type assignable to the return type of the function.

May also be used inside an ISR, in which case the expression is always
disallowed.


``if``
~~~~~~

Usage: ::

  if <expression> then
    [...]
  [elseif <expression> then
    [...]]
  [elseif...]
  [else
    [...]]
  end

Causes at most one of the blocks provided to execute. Expressions are tested in
order, and the first expression to evaluate to ``true`` causes the corresponding
block to be executed. If none of the expressions evalute to ``true``, the block
beginning with ``else`` is executed, if present. Once an expression which
evaluates to ``true`` is executed, the rest of the expressions will not be
evaluated.

Each branch introduces a new scope.


``while``
~~~~~~~~~

Usage: ::

  while <expression> do
    [...]
  end

Introduces a loop which executes the provided block zero or more times. The
block is executed repeatedly until the expression evaluates to ``false``, or the
loop is terminated.

The provided block introduces a new scope.


``for``
~~~~~~~

Usage: ::

  for <identifier> : <type> in <expression> do
    [...]
  end

Evaluates the given expression once, which must be of type array or slice, then
introduces a loop which executes the provided block once for each element of the
value of the expression, with the provided identifier bound to the value of the
element.

The provided block introduces a new scope.


``break``
~~~~~~~~~

Usage: ::

  break

Terminates the innermost loop currently executing. It is an error to have a
``break`` statement outside of a loop.


``continue``
~~~~~~~~~~~~

Usage: ::

  continue

Terminates the currently-executing block, but does not terminate the loop,
instead causing it to move to the next iteration if any remain. It is an error
to have a ``continue`` statement outside of a loop.


Type Expressions
----------------

Primitive Types
~~~~~~~~~~~~~~~

Primitive types are provided for signed and unsigned integers for 8-bit, 16-bit,
24-bit, and 32-bit integers. They are written as follows: ::

  u8 u16 u24 u32
  i8 i16 i24 i32

(Types beginning with ``u`` are unsigned.) Primitive types are as wide as the
number of bits divided by eight.


Array Types
~~~~~~~~~~~

Array types are written as: ::

  [<base>; <start> to <end>]    /* first form */
  [<base>; <end>]               /* second form */

where ``<base>`` is another type, ``<start>`` and ``<end>`` are the lower and
upper bounds, respectively, where the lower bound is inclusive and upper bound
is exclusive. In the second form, ``<start>`` is implied to be ``0``.

The width of an array type is the width of ``<base>`` multiplied by the
difference between ``<end>`` and ``<start>``. (For example, ``[u8; 3 to 7]`` is
four bytes wide.)


Pointer and Slice Types
~~~~~~~~~~~~~~~~~~~~~~~

Pointer types are constructed by prefixing a non-array type with a ``&``, for
example, ``&u8`` is a pointer to an 8-bit unsigned type. Pointers are always two
bytes wide.

Slice types take the form of ``&[<base>]``. Slices have a built-in length, and
are always four bytes wide. Taking a pointer to an array produces a slice.


Value Expressions
-----------------

Expressions are written infix, similar to 'C'. Operations are resolved in the
following order. ::

  (<expr>)

Parenthesised expressions are resolved from innermost out. Whitespace is allowed
but not required around parentheses. ::

  <expr>[<expr>]

Indexes into an array. The expression on the left must resolve to an array or
slice type, and the expression on the right must resolve to a ``u8`` or ``u16``.
::

   <fun>([<expr>[, ...]])

Calls a function. ``<fun>`` must be an expression which evaluates to a function
or function pointer. Expressions are evaluated and passed as arguments, and the
function expression resolves to the return value of the function. ::

  &<expr>
  @<expr>

Takes a pointer to a value, and dereferences a pointer, respectively. ::

  bitnot <expr>
  <expr> bitand <expr>
  <expr> bitor <expr>
  <expr> bitxor <expr>

Bitwise operations are provided for unsigned types. For dyadic operations, both
sides must be the same width. ::

  <expr> << <known-expr>
  <expr> >> <known-expr>

Left-shift and right-shift operations, respectively. The right-hand side must be
known at compile-time. ::

  <expr> * <expr>
  <expr> / <expr>

Multiplication and division of integer types. ::

  <expr> + <expr>
  <expr> - <expr>

Addition and subtraction of integer types. ::

  <expr> == <expr>
  <expr> != <expr>
  <expr> <= <expr>
  <expr> >= <expr>
  <expr> < <expr>
  <expr> > <expr>

Comparison operators. Evaluates to a boolean value. ::

  <expr> = <expr>

Assignment operator. The left-hand side must be a bare name, a dereference, or
an index expression.
