==============================
 *jeff65* Calling Conventions
==============================

This document defines the calling convention for *jeff65*-supported languages
(in particular, gold-syntax).

.. note:: This document is an early draft. It is expected to change as
          implementation progresses.

To propose a change to this document, create a pull request from a branch with a
name beginning with ``spec-gold-``, which contains the edits to this document
relevant to enact the change, and if possible, the necessary alterations to the
parser and/or lexer. (If those changes would be high-effort, open a bug once the
PR has been accepted.)

.. contents::


General Considerations
======================

The primary consideration for 6502 calling conventions is that the stack is
small---only 256 bytes (one page). This can be handled in two ways---either
using a synthetic stack pointer in the zero page, or by heavily limiting the use
of the stack.

A secondary consideration is code size. Ideally, jeff65-generated executables
would be comparable in size to hand-assembled code; one should not find oneself
in a position where many functions have to be translated into assembly in order
to fit into the machine.

We therefore take a hybrid approach, and distinguish between recursive functions
and non-recursive functions, with initial support focusing on non-recursive
functions.

Finally, calling conventions can limit what is allowed in the language; for
example, callee-cleans conventions often cannot support variable-length argument
lists.


Syntax & Linker Considerations
------------------------------

As stated above, we plan to support multiple calling conventions. In order to
avoid chaos, the convention will be part of the the type of functions, which is
included in compiled units. Therefore, there is no chance of a header/binary
calling convention mismatch.

Calling conventions will be versioned. This allows us to adjust the calling
conventions in the future while still allowing previous binaries to be linked.

The linker is responsible for ensuring that at least six bytes of stack are
available for interrupts at all times. In addition, the linker must respect
stack space reservations for functions. 

If the linker can prove that it will not cause a collision, then it may share a
static location between two functions, e.g. suppose function ``foo`` calls
functions ``bar`` and ``baz``, which each call function ``zed``. In this case,
the reservations for ``bar`` and ``baz`` may overlap with each other.


Calling Conventions
===================

``c64-static-call-0``
---------------------

This calling convention is the default calling convention for functions declared
in gold-syntax using the ``fun`` keyword, targeting the Commodore 64.

- The return address is placed onto the hardware stack, typically via the
  ``JSR`` instruction.

- Each function indicates to the linker that a certain number of bytes must be
  reserved in memory for local variables and arguments.

- Arguments are placed into reserved memory before calling the function.
  Reserved memory is not otherwise initialized by the caller. The first two
  8-bit-wide arguments are placed into the X and Y registers, respectively.

- Zero-page addresses $00fd and $00fe are reserved for use by functions which
  require them, but must be saved and restored around function calls by the
  caller.

- Zero-page address $00fb-$00fc are a little-endian pointer to the location
  of the return value. This must be saved and restored around function calls by
  the caller if necessary.

- 8-bit-wide return values placed in the X register.

- The caller is responsible for preserving registers it needs.

- The function may use no more than 50 bytes of stack space for temporaries. The
  amount that it actually uses should be indicated to the linker.

- Functions using this calling convention may call any other function in the
  ``c64`` family, unless it would result in insufficient stack space for
  interrupts and the called function. Functions using this calling convention
  may not call themselves or any function which calls them, directly or
  indirectly.

- **TODO** Status register?


``c64-isr-call-0``
------------------

This calling convention is the default calling convention for functions declared
in gold-syntax using the ``isr`` keyword, targeting the Commodore 64.

.. note:: This section needs expansion.

- No arguments or return values are allowed.

- Each function indicates to the linker that a certain number of bytes must be
  reserved in memory for local variables.

- Called function is responsible for preserving registers A, X, and Y, which are
  pushed onto the stack in that order.

- Functions using this calling convention may not call functions in the
  ``c64-static-call`` or ``c64-isr-call`` families.
