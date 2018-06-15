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

Data described as "in-band" refers to data stored inside the structure being
discussed, while data described as "out-of-band" refers to data stored in some
other location indicated by an offset.

A box like this represents a single byte: ::

  0    1
  +----+
  |    |
  +----+

The vertical bars will be left out if a multibyte value is being described, but
the numbers and ``+`` dividers will be used.

A box like this, with ``=`` signs, represents a variable-width field: ::

  0    ...    n
  +===========+
  |           |
  +===========+

The above diagram describes a field which is *n* bytes long. If *n* is negative,
then the absolute value is used; negative length values, where allowed, indicate
that the data in the field is zlib-compressed. Note that the length refers to
the length of the *compressed* data, not the uncompressed data.

A dotted box indicates that an unknown number of fields have been omitted: ::

  0    ...    y    ...    z
  +-- - - - --+== = = = ==+
  |           |           |
  +-- - - - --+== = = = ==+

A dotted line of ``-`` indicates that the omitted fields are of known size,
while a dotted line of ``=`` indicates that the omitted fields are of unknown
size.


File Format
===========

Very Primitive Values
---------------------

Numbers wider than 1 byte are stored in little-endian (LSB-first) format. This
is for consistency with the 6502 processor, which is itself little-endian on the
occasions that it uses a value wider than 1 byte. Numbers are fixed-width.
Negative numbers, where allowed, are stored in two's-complement format.


Basic File Structure
--------------------

All offsets are bytes from the beginning of the file. Offsets and lengths are
unsigned 32-bit integers unless otherwise stated. Offsets must be less than the
length of the file.

All CRC32 values are calculated in a manner consistent with Gzip, Zlib, PKZIP,
etc. The parser is expected to check these values. If they fail to match,
parsing should stop immediately.

Blum archives begin with a 16-byte header section, laid out as follows: ::

  0    1    2    3    4    5    6    7    8
  +----+----+----+----+----+----+----+----+
  |0x93| 'Blm'        |0x0d|0x0a|0x1a|0x0a|
  +----+----+----+----+----+----+----+----+

  8    9   10   11   12   13   14   15   16   17   18   19   20
  +----+----+----+----+----+----+----+----+----+----+----+----+
  | Entry 0 offset    | Entry 0 Length    | Entry 0 CRC32     |
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

The offset indicates the start of the first entry (entry 0) in bytes starting
from the beginning of the file, e.g. if it was 16, then the entry would be
located directly after the header.

Except for the header, all data items may be located anywhere in the file in no
particular order. This allows the writer some flexibility when generating the
file. In addition, the file may contain data which is not accessible by
traversing the entry structures. The parser is expected to ignore this data.

Entries are laid out as follows: ::

  0    1    2    3    4    5    6    7    8    9   10   11   12
  +----+----+----+----+----+----+----+----+----+----+----+----+
  | Data offset       | Data Length       | Data CRC32        |
  +----+----+----+----+----+----+----+----+----+----+----+----+

  12  13   14   15   16   17   18   19   20   21   22   23   24
  +----+----+----+----+----+----+----+----+----+----+----+----+
  | Next entry offset | Next Entry Length | Next entry CRC32  |
  +----+----+----+----+----+----+----+----+----+----+----+----+

  24  25   26   27   28   ...  28+n
  +----+----+----+----+===========+
  | Name length       | Name data |
  +----+----+----+----+===========+

Entries form a linked list, with each entry pointing to the next entry. The last
entry should have its "next entry" fields all set to 0.

The data pointed to by the "data offset" field is `union layout`_ data allowing
only an `Sy struct`_. These contain other nested structures; when calculating
the CRC32, these are included. In the future, other entry types may be allowed;
when encountering an unrecognized entry type, the parser should skip it, and
should not attempt to parse the struct.

The "name length" field is a 32-bit signed integer, but negative values are
currently reserved for future use. If the parser encounters a negative value, it
should issue a warning and skip the entry.

Note that entries may include trailing data after the name data field. This is
allowed, and the data must be included in the CRC32 but not otherwise parsed.

Entry order is not important, and two archive files with the same entries in a
different order may be considered equivalent. However, when manipulating archive
files, entry order should be preserved if possible to allow convenient diffing.

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

  0    1    2    3    4     ...   4+n
  +----+----+----+----+=============+
  | Length = n        | String data |
  +----+----+----+----+=============+

The length field is an signed 4-byte integer, and its value must match the byte
length of the encoded string data. A negative value indicates that the data is
zlib-compressed.

Despite being called "short" strings, rather long strings may be stored in this
structure. It is, however, not recommended. If compression is used, the size of
the decompressed data must not exceed 2 GiB, i.e. the maximum length allowed for
uncompressed data. If the parser encounters a string longer than this, then it
should issue a warning and truncate the string.

.. _`RFC 3629`: https://tools.ietf.org/html/rfc3629


Blob Data
~~~~~~~~~

Blob data are stored out-of-band, at a file location indicated by a length and
offset field. ::

  0   1   2   3   4   5   6   7   8   9  10  11  12
  +---+---+---+---+---+---+---+---+---+---+---+---+
  | Offset        | Length        | CRC32         |
  +---+---+---+---+---+---+---+---+---+---+---+---+

The offset is a 32-bit unsigned integer, and the length is a 32-bit signed
integer. The sum of the offset and the length must be less than or equal to the
size in bytes of the archive.

Negative lengths indicate the use of zlib compression. The CRC32 is calculated
based on actual file data, i.e. if the data is compressed, the CRC32 is computed
based off of the compressed data. If compression is used, the size of the
decompressed data must not exceed 2 GiB, i.e. the maximum length allowed for
uncompressed data. If the parser encounters a blob longer than this, then it
should stop parsing the archive with an error.


Layouts
-------

Complex values are structured using one of the layouts below.


Array Layout
~~~~~~~~~~~~

An array allows zero or more values of the same type to be stored together. The
sizes of the values may not be known in advance, and may vary. ::

  0    1    2    3    4    ...    x    ...    y    ...    z
  +----+----+----+----+===========+== = = = ==+===========+
  | Count = n         | Value 0   |    ...    | Value n-1 |
  +----+----+----+----+===========+== = = = ==+===========+

The count field is an unsigned 32-bit integer. The only way to find the end of
the array is to parse through all of the objects.

Arrays may contain objects of any type, including other arrays, `struct layout`_
data, etc.


Table Layout
~~~~~~~~~~~~

A table allows zero or more key-value pairs to be stored together, where all
keys are the same type and all values are the same type. The sizes of the values
may not be known in advance, and may vary. ::

  0   1   2   3   4  ...  v    ...    w ... x   ...   y    ...    z
  +---+---+---+---+=======+===========+= = =+=========+===========+
  | Count = n     | Key 0 | Value 0   | ... | Key n-1 | Value n-1 |
  +---+---+---+---+=======+===========+= = =+=========+===========+

The count field is an unsigned 32-bit integer. The only way to find the end of
the table is to parse through all of the objects.

Table values be objects of any type, including arrays, `struct layout`_ data,
etc., while key types are limited to `short string`_ and integer.

Tables are ordered, and the parser must preserve the order of the table entries.


Struct Layout
~~~~~~~~~~~~~

A struct allows zero or more values of different types to be stored together,
structured as a series of key-value pairs. The sizes of the values may not be
known in advance, and may vary. ::

  0     1     2   3   4   ...   x   ...   y  y+1  y+2    ...    z
  +-----+-----+---+---+=========+-- - = ==+----+----+===========+
  | Count = n | Key 0 | Value 0 |   ...   | Key n-1 | Value n-1 |
  +-----+-----+---+---+=========+-- - = ==+----+----+===========+

The count field is an unsigned 16-bit integer. Each key is a 2-byte value, where
each byte is a lowercase alphanumeric ASCII character. The type of the values,
and therefore how they must be parsed, are determined by a combination of the
struct type and the key.

The only way to find the end of the struct is to parse through all of the
objects. The value fields of a struct may contain objects of any type, including
other structs.

Note that the type code is *not* part of the struct layout; it is only used as
part of `union layout`_.

Values with unrecognized keys are to be ignored. This allows keys to be added in
the future while keeping backwards-compatibility. If a key is repeated, then the
value provided later in the file should be used.

Structs are unordered. Two structs with the same key-value pairs in a different
order are considered equivalent. However, software which manipulates archives
should preserve the order of the key-value pairs if possible.


Union Layout
~~~~~~~~~~~~

A union allows a single value in struct layout to be stored with a type
indicator. The size of the value is determined by its type. ::

  0    1    2    ...    z
  +----+----+===========+
  | Type    | Value     |
  +----+----+===========+

The type field is a 2-byte value, where the first byte is an uppercase
alphabetical ASCII character and the second byte is a lowercase alphanumeric
ASCII character. The type of the value, and therefore how it must be parsed, is
determined by the type code.

The only way to find the end of the union is to parse through the object. The
value field must be in `struct layout`_ of the given type.


Complex Values
--------------

``Sy`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Sy`` represents a symbol which may be re-used
in other units.

+--------+------------------------------+-----------------------------------------------+
| Key    | Type                         | Description                                   |
+========+==============================+===============================================+
| ``sc`` | `Short String`_              | The section the symbol should be linked into. |
+--------+------------------------------+-----------------------------------------------+
| ``ty`` | `Type Union`_                | The type of the symbol.                       |
+--------+------------------------------+-----------------------------------------------+
| ``re`` | Table of unsigned 2-byte     | The relocations required to link the symbol.  |
|        | integer and `Re struct`_     |                                               |
+--------+------------------------------+-----------------------------------------------+
| ``da`` | `Blob Data`_                 | The data associated with the symbol.          |
+--------+------------------------------+-----------------------------------------------+

The blob in the ``da`` field may not be larger than 64 KiB.


``Re`` Struct
~~~~~~~~~~~~~

A `struct layout`_ value of type ``Re`` represents a relocation, i.e. a symbolic
representation of a memory location which must be resolved by the linker.

+--------+------------------------------+--------------------------------------------------+
| Key    | Type                         | Description                                      |
+========+==============================+==================================================+
| ``sy`` | `Short String`_              | The name of the symbol to link against.          |
+--------+------------------------------+--------------------------------------------------+
| ``ic`` | 16-bit signed integer        | The value by which to increment the named        |
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
