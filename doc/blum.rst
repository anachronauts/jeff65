============================
 Blum Archive Specification
============================

This document defines the structure of compiled blum object files output by the
jeff65 compiler.

To propose a change to this document, create a pull request from a branch with a
name beginning with ``spec-blum-``, which contains the edits to this document
relevant to enact the change, and if possible, the necessary alterations to the
reader and/or writer. (If those changes would be high-effort, open a bug once
the PR has been accepted.)

.. contents::


Conventions
===========

Where literal strings are used, in the context of file data, they represent a
sequence of bytes. Non-ASCII bytes are represented using the escape sequence
``\x##``, where ``##`` is replaced by a hexadecimal byte value. (This is as in
Python.)

Where bytes are numbered, they are numbered starting from zero, starting from
the byte closest to the beginning of the file. Thus a four-byte datum would have
its bytes numbered 0, 1, 2, and 3, in that order.

Data described as "in-band" refers to data stored in the "entry" section of the
file (see `File Structure`_), while data described as "out-of-band" refers to
data stored in the "blobs" section of the file.


File Format
===========

Very Primitive Values
---------------------

Numbers wider than 1 byte are stored in little-endian (LSB-first) format. This
is for consistency with the 6502 processor, which is itself little-endian on the
occasions that it uses a value wider than 1 byte. Numbers are fixed-width.
Negative numbers, where allowed, are stored in two's-complement format.


File Structure
--------------

A blum archive is structured as follows: ::

  +---------------------------------------------+
  | Header (12 bytes)                           |
  +---------------------------------------------+
  | Entry 0 (union of Constant, Symbol)         |
  :                                             :

  :                                             :
  | Entry (count - 1)                           |
  +---------------------------------------------+
  | Blobs (freeform bytes referenced using      |
  |        offsets from beginning of file)      |
  +---------------------------------------------+

The header is as follows: ::

  0    1    2    3    4    5    6    7    8    9   10   11   12
  +----+----+----+----+----+----+----+----+----+----+----+----+
  |0x93| 'Blm'        |0x0d|0x0a|0x1a|0x0a| Entry count       |
  +----+----+----+----+----+----+----+----+----+----+----+----+

The first eight bytes of the header are worth explaining. It is lifted from the
PNG specification, with the first four bytes changed to appropriate values.

 * The leading byte ``\x93`` has the high-bit set, to detect transmission
   through non-8-bit-clean channels. [#]_
 * Bytes 1 through 3, ``Blm``, indicates that this is a blum archive. A mix of
   capital and lowercase letters are used to detect casefolding.
 * Bytes 4 and 5, ``\x0d\x0a``, are a DOS line ending. This detects DOS-to-UNIX
   conversion.
 * Byte 6, ``\x1a``, causes the DOS *type* command to consider this the end of the
   file, to avoid spewing garbage into the user's terminal.
 * Byte 7, ``\x0a``, is a UNIX line ending. This detects UNIX-to-DOS conversion.

Thus, various adulterations of the file may be detected.

Each entry is stored in `union layout`_, with allowed types being a `Cn struct`_
or a `Sy struct`_. See the appropriate sections for a discussion of the
particulars of how these objects are arranged.

Entries are contiguous, with the first entry beginning immediately after the
entry count, and each subsequent entry beginning after the preceding one. There
must be at least as many entries as specified in the header, though entries
above and beyond the given number will not be read and will be considered part
of the blobs section.

The blobs section consists of zero or more bytes, beginning immediately after
the last entry. This area is used to store entry data out-of-band from the
entries themselves. In particular, machine code is stored in this area. The
blobs section has no particular layout. Out-of-band data is indicated using an
offset from the beginning of the file and a length in bytes, as described in
`Blob Data`_.

.. [#] 1993 is the year *Jurassic Park* was released, starring Jeff Goldblum as
       Dr. Ian Malcolm.


Primitive Values
----------------

As mentioned above in `Very Primitive Values`_, integers are stored in
little-endian two's-complement format.


Short String
~~~~~~~~~~~~

Short strings are stored in-band as a length followed by the string data,
encoded as zero or more UTF-8 bytes (see `RFC 3629`_), as follows: ::

  0    1    2    3    4    5    ...    n
  +----+----+----+----+----+-- - - - --+
  | Length = n        | Data ...       |
  +----+----+----+----+----+-- - - - --+

The length field is an unsigned 4-byte integer, and its value must match the
byte length of the encoded string data.

.. _`RFC 3629`: https://tools.ietf.org/html/rfc3629


Blob Data
~~~~~~~~~

Blobs are stored out-of-band, and are restricted in length to 64 KiB (65536
bytes). The in-band part of a blob consists of an offset from the beginning of
the archive file, and a length field. ::

  0    1    2    3    4    5    6
  +----+----+----+----+----+----+
  | Offset            | Length  |
  +----+----+----+----+----+----+

The offset is a 4-byte unsigned integer, and the length is a 2-byte unsigned
integer. The sum of the offset and the length must be less than or equal to the
size in bytes of the archive.

The offset should point into the blobs section of the archive, though this is
not strictly necessary. Blobs may overlap, and there may exist ranges in the
blobs section which are not referred to by any entry.


Layouts
-------

Complex values are structured using one of the layouts below.


Array Layout
~~~~~~~~~~~~

An array allows zero or more values of the same type to be stored together. The
sizes of the values may not be known in advance, and may vary. ::

  0    1    2    3    4    ...    x    ...    y    ...    z
  +----+----+----+----+-- - - - --+-- - - - --+-- - - - --+
  | Count = n         | Value 0   | ...       | Value n-1 |
  +----+----+----+----+-- - - - --+-- - - - --+-- - - - --+

The count field is an unsigned 4-byte integer. The only way to find the end of
the array is to parse through all of the objects.

Arrays may contain objects of any type, including other arrays, `struct layout`_
data, etc.


Table Layout
~~~~~~~~~~~~

A table allows zero or more key-value pairs to be stored together, where all
keys are the same type and all values are the same type. The sizes of the values
may not be known in advance, and may vary. ::

  0    1    2    3    4  ...  v    ...    w ... x   ...   y    ...    z
  +----+----+----+----+-- - --+-- - - - --+- - -+-- - - --+-- - - - --+
  | Count = n         | Key 0 | Value 0   | ... | Key n-1 | Value n-1 |
  +----+----+----+----+-- - --+-- - - - --+- - -+-- - - --+-- - - - --+

The count field is an unsigned 4-byte integer. The only way to find the end of
the table is to parse through all of the objects.

Tables values be objects of any type, including arrays, `struct layout`_ data,
etc., while key types are limited to `short string`_ and integer.


Struct Layout
~~~~~~~~~~~~~

A struct allows zero or more values of different types to be stored together,
structured as a series of key-value pairs. The sizes of the values may not be
known in advance, and may vary. ::

  0    1    2    3    4
  +----+----+----+----+-
  | Count = n         |
  +----+----+----+----+-

   4    5    6    ...    x
  -+----+----+-- - - - --+-
   | Key 0   | Value 0   |   ...
  -+----+----+-- - - - --+-

   y   y+1  y+2   ...    z
  -+----+----+-- - - - --+
   | Key n-1 | Value n-1 |
  -+----+----+-- - - - --+

The count field is an unsigned 4-byte integer. Each key is a 2-byte value, where
each byte is a lowercase alphanumeric ASCII character. The type of the values,
and therefore how they must be parsed, are determined by a combination of the
struct type and the key.

The only way to find the end of the struct is to parse through all of the
objects. The value fields of a struct may contain objects of any type, including
other structs.

Note that the type code is *not* part of the struct layout; it is only used as
part of `union layout`_.

Fields with unrecognized keys are to be ignored. This allows fields to be added
in the future while keeping backwards-compatibility.


Union Layout
~~~~~~~~~~~~

A union allows one value to be stored with a type indicator associated with it.
The size of the value is determined by its type. ::

  0    1    2    ...    z
  +----+----+-- - - - --+
  | Type    | Value     |
  +----+----+-- - - - --+

The type field is a 2-byte value, where the first byte is an uppercase
alphabetical ASCII character and the second byte is a lowercase alphanumeric
ASCII character. The type of the value, and therefore how it must be parsed, is
determined by the type code.

The only way to find the end of the union is to parse through the object. The
value field must be in `struct layout`_ of the given type.


Complex Values
--------------

``Cn`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Cn`` represents a constant symbol which may
be re-used in other units.

+--------+-----------------+---------------------------+
| Key    | Type            | Description               |
+========+=================+===========================+
| ``nm`` | `Short String`_ | The name of the constant. |
+--------+-----------------+---------------------------+
| ``ty`` | `Type Union`_   | The type of the constant. |
+--------+-----------------+---------------------------+
| ``vl`` | Raw 8 bytes     | The value of the constant.|
+--------+-----------------+---------------------------+

The ``vl`` key indicates a field of fixed length which is interpreted depending
on the value of ``ty``.


``Sy`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Sy`` represents a symbol which may be re-used
in other units.

+--------+------------------------------+-----------------------------------------------+
| Key    | Type                         | Description                                   |
+========+==============================+===============================================+
| ``nm`` | `Short String`_              | The name of the symbol.                       |
+--------+------------------------------+-----------------------------------------------+
| ``sc`` | `Short String`_              | The section the symbol should be linked into. |
+--------+------------------------------+-----------------------------------------------+
| ``ty`` | `Type Union`_                | The type of the symbol.                       |
+--------+------------------------------+-----------------------------------------------+
| ``re`` | Table of unsigned 2-byte     | The relocations required to link the symbol.  |
|        | integer and `Re struct`_     |                                               |
+--------+------------------------------+-----------------------------------------------+
| ``da`` | `Blob Data`_                 | The data associated with the symbol.          |
+--------+------------------------------+-----------------------------------------------+


``Re`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Re`` represents a relocation, i.e. a symbolic
representation of a memory location which must be resolved by the linker.

+--------+------------------------------+--------------------------------------------------+
| Key    | Type                         | Description                                      |
+========+==============================+==================================================+
| ``sy`` | `Short String`_              | The name of the symbol to link against.          |
+--------+------------------------------+--------------------------------------------------+
| ``ic`` | 2-byte signed integer        | The value by which to increment the named        |
|        |                              | address.                                         |
+--------+------------------------------+--------------------------------------------------+
| ``by`` | One of 'w', 'h', or 'l'      | The address segment (full, high part, low part). |
+--------+------------------------------+--------------------------------------------------+


Type Union
~~~~~~~~~~

A `union layout`_ value containing one of the following:

 * `Ph struct`_
 * `Vd struct`_
 * `In struct`_
 * `Rf struct`_
 * `Fn struct`_


``Ph`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Ph`` represents an instance of the "phantom"
type. It has no fields, so it always serializes as four zero bytes.


``Vd`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Vd`` represents an instance of the "void"
type. It has no fields, so it always serializes as four zero bytes.


``In`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``In`` represents an instance of one of the
integer types.

+--------+------------------------------+--------------------------------------------------+
| Key    | Type                         | Description                                      |
+========+==============================+==================================================+
| ``wd`` | 1-byte unsigned integer      | The width, in bytes, of the type.                |
+--------+------------------------------+--------------------------------------------------+
| ``sg`` | One of 0x00 or 0x01          | 0x01 if the type is signed, 0x00 otherwise.      |
+--------+------------------------------+--------------------------------------------------+


``Rf`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Rf`` represents an instance of a reference type.

+--------+------------------------------+--------------------------------------------------+
| Key    | Type                         | Description                                      |
+========+==============================+==================================================+
| ``tg`` | `Type Union`_                | The type of the reference target.                |
+--------+------------------------------+--------------------------------------------------+


``Fn`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Fn`` represents an instance of a function type.

+--------+------------------------------+--------------------------------------------------+
| Key    | Type                         | Description                                      |
+========+==============================+==================================================+
| ``rt`` | `Type Union`_                | The return type.                                 |
+--------+------------------------------+--------------------------------------------------+
| ``as`` | Array of `Type Union`_       | The types of the arguments.                      |
+--------+------------------------------+--------------------------------------------------+
