# jeff65 immutable datatypes
# Copyright (C) 2018  jeff65 maintainers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bisect
import collections.abc


class FrozenDict(collections.abc.Mapping):
    """An immutable mapping type.

    Currently this is implemented as a sorted list, but in the future it could
    be replaced with a more efficient implementation if it proves to be slow.
    """

    def __init__(self, keys, values):
        self.__keys = tuple(keys)
        self.__values = tuple(values)

    def __repr__(self):
        pairs = ", ".join(f'{k!r}: {v!r}' for k, v in self.items())
        return f'FrozenDict({{{pairs}}})'

    def __iter__(self):
        return iter(self.__keys)

    def __len__(self):
        return len(self.__keys)

    def __getitem__(self, key):
        k = bisect.bisect_left(self.__keys, key)
        if k != len(self.__keys) and self.__keys[k] == key:
            return self.__values[k]
        raise KeyError(key)

    def add(self, key, value):
        builder = self.asbuilder()
        builder[key] = value
        return builder.asfrozen()

    def update(self, mapping):
        builder = self.asbuilder()
        builder.update(mapping)
        return builder.asfrozen()

    def remove(self, key):
        builder = self.asbuilder()
        del builder[key]
        return builder.asfrozen()

    def asbuilder(self):
        return self.Builder(self.__keys, self.__values)

    @classmethod
    def empty(cls):
        return cls((), ())

    @classmethod
    def create(cls, other):
        if isinstance(other, cls):
            return other  # No need to re-create!
        elif isinstance(other, cls.Builder):
            return other.asfrozen()

        builder = cls.Builder.empty()
        builder.update(other)
        return builder.asfrozen()

    class Builder(collections.abc.MutableMapping):
        def __init__(self, keys, values):
            self.__keys = list(keys)
            self.__values = list(values)

        def __repr__(self):
            pairs = ", ".join(f'{k!r}: {v!r}' for k, v in self.items())
            return f'FrozenDict.Builder({{{pairs}}})'

        def __iter__(self):
            return iter(self.__keys)

        def __len__(self):
            return len(self.__keys)

        def __getitem__(self, key):
            k = bisect.bisect_left(self.__keys, key)
            if k != len(self.__keys) and self.__keys[k] == key:
                return self.__values[k]
            raise KeyError(key)

        def __setitem__(self, key, value):
            k = bisect.bisect_left(self.__keys, key)
            if k != len(self.__keys) and self.__keys[k] == key:
                self.__keys[k] = key
                self.__values[k] = value
            else:
                self.__keys.insert(k, key)
                self.__values.insert(k, value)

        def __delitem__(self, key):
            k = bisect.bisect_left(self.__keys, key)
            if k != len(self.__keys) and self.__keys[k] == key:
                del self.__keys[k]
                del self.__values[k]
            else:
                raise KeyError(key)

        def unsafeset(self, key, value):
            self.__keys.append(key)
            self.__values.append(value)

        def asfrozen(self):
            return FrozenDict(self.__keys, self.__values)

        @classmethod
        def empty(cls):
            return cls([], [])
