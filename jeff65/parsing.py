# jeff65 parser generator
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

import attr
import logging
import re
import time
from itertools import chain

logger = logging.getLogger(__name__)


class ParseError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@attr.s(slots=True, frozen=True)
class TextSpan:
    start_line = attr.ib()
    start_column = attr.ib()
    end_line = attr.ib()
    end_column = attr.ib()

    def __attrs_post_init__(self):
        assert self.end >= self.start

    @property
    def start(self):
        return (self.start_line, self.start_column)

    @property
    def end(self):
        return (self.end_line, self.end_column)

    def __bool__(self):
        return self.start < self.end

    def __contains__(self, other):
        return (
            isinstance(other, TextSpan)
            and self.start <= other.start
            and other.end <= self.end)

    @staticmethod
    def cover(spans):
        """Return a TextSpan covering all of the given spans.

        The result is the shortest span t such that every given is contained in
        it. Note that because TextSpans are always contiguous, there may exist
        spans which are not contained in any of the given spans, but are
        contained in the cover span.
        """
        return TextSpan(
            *min(s.start for s in spans),
            *max(s.end for s in spans))

    def __str__(self):
        start = f'{self.start_line}:{self.start_column}'
        end = f'{self.end_line}:{self.end_column}'
        return f'{start}-{end}'


@attr.s(slots=True, frozen=True)
class Token:
    t = attr.ib()
    text = attr.ib()
    channel = attr.ib(default=0, cmp=False)
    span = attr.ib(default=None, cmp=False)

    def _pretty(self, indent, no_position):
        i = " " * indent
        return f'{i}{self.t}={self.text!r} {self.span}\n'


class ReStream:
    """Regex-matchable stream."""

    CHANNEL_ALL = -1
    CHANNEL_DEFAULT = 0
    CHANNEL_HIDDEN = 1

    def __init__(self, stream):
        self.stream = iter(stream)
        self.current = None
        self.line = 0
        self.column = 0

        try:
            self.advance_line()
        except StopIteration:
            self.current = ""
            self.line = 1

    def advance_line(self):
        """Advance the stream position to the beginning of the next line."""
        try:
            self.current = next(self.stream)
        except StopIteration:
            raise
        else:
            self.line += 1
            self.column = 0

    def assure_line(self):
        """Assures that at least one character remains in the current line."""
        if self.column == len(self.current):
            self.advance_line()

    def match(self, regex):
        """Match the given regex at the current stream position.

        In order to actually advance the position, call ReStream.produce() with
        the returned match object.

        Returns a match object if successful, None otherwise.
        """

        self.assure_line()
        return regex.match(self.current, self.column)

    def produce(self, symbol, match, channel=CHANNEL_DEFAULT):
        """Produce a token and advance the position."""

        token = Token(symbol, match.group(), channel,
                      TextSpan(
                          self.line, self.column,
                          self.line, match.end()))
        self.column = match.end()
        return token

    def rewind(self, token: Token):
        """Rewinds by one token.

        This may only be called if the last method to be called on the ReStream
        object was the produce() call which returned the given token.
        """

        assert token.span.end == (self.line, self.column)
        self.column = token.span.start_column

    def produce_eof(self, symbol):
        """Produce an EOF token."""
        return Token(symbol, None, self.CHANNEL_ALL,
                     TextSpan(self.line, self.column, self.line, self.column))


class Lexer:
    def __init__(self, eof, rules):
        """Create a lexer callable.

        rules should be a list of tuples of one of the following forms:
          (pattern, token_type)
          (mode, pattern, token_type)
          (mode, pattern, token_type, channel)
        """

        self.eof = eof
        self.mode_rules = {}
        for mptc in rules:
            mode, channel = Parser.NORMAL_MODE, ReStream.CHANNEL_DEFAULT
            if len(mptc) == 2:
                pattern, tt = mptc
            elif len(mptc) == 3:
                mode, pattern, tt = mptc
            else:
                mode, pattern, tt, channel = mptc
            rs = self.mode_rules.setdefault(mode, [])
            rs.append((re.compile(pattern), tt, channel))

    def __call__(self, stream: ReStream, mode: int) -> Token:
        try:
            stream.assure_line()
        except StopIteration:
            return stream.produce_eof(self.eof)

        for regex, tt, channel in self.mode_rules[mode]:
            m = stream.match(regex)
            if m:
                return stream.produce(tt, m, channel)
        assert False, "no match!"  # TODO: proper exception


def _convert_lhs(lhs):
    if not isinstance(lhs, Symbol):
        return Symbol(lhs)
    return lhs


def _convert_rhs(rhs):
    result = []
    for sym in rhs:
        if isinstance(sym, tuple):
            # alternations are tuples
            sym = frozenset(_convert_lhs(s) for s in sym)
        elif isinstance(sym, frozenset):
            # already converted
            pass
        else:
            sym = frozenset({_convert_lhs(sym)})
        result.append(sym)
    return tuple(result)


@attr.s(slots=True, frozen=True, repr=False)
class Symbol:
    value = attr.ib()

    @property
    def is_terminal(self):
        # we represent bare nonterminals as strings
        return not isinstance(self.value, str)

    def __repr__(self):
        return f"`{self.value}"

    def extend(self, start, end):
        return ExtendedSymbol(self.value, start, end)

    @property
    def parent(self):
        return Symbol(self.value)


@attr.s(slots=True, frozen=True, repr=False)
class ExtendedSymbol(Symbol):
    start = attr.ib()
    end = attr.ib()

    def __repr__(self):
        return f"`{self.start}_{self.value!r}_{self.end}"


@attr.s(slots=True, frozen=True, repr=False)
class Rule:
    lhs = attr.ib(converter=_convert_lhs)
    rhs = attr.ib(converter=_convert_rhs)
    prec = attr.ib(default=None)
    rassoc = attr.ib(default=False)
    mode = attr.ib(default=0)  # Parser.NORMAL_MODE
    pointer = attr.ib(default=None)
    parent = attr.ib(default=None)

    def with_pointer(self, pointer):
        return attr.evolve(self, pointer=pointer)

    @property
    def next_symbols(self):
        if self.pointer is None:
            raise Exception('Rule has no pointer')
        elif self.pointer == len(self.rhs):
            return frozenset()
        return self.rhs[self.pointer]

    @property
    def advanced(self):
        if self.pointer is None:
            raise Exception('Rule has no pointer')
        elif self.pointer == len(self.rhs):
            raise Exception('Rule cannot be advanced')
        return self.with_pointer(self.pointer + 1)

    def __repr__(self):
        syms = []
        for sym in self.rhs:
            if len(sym) == 1:
                syms.append(str(next(iter(sym))))
            else:
                alts = ' | '.join(str(s) for s in sym)
                syms.append(f'({alts})')
        if self.pointer is not None:
            syms.insert(self.pointer, '.')
        rhs = ' '.join(syms)
        if self.prec is not None:
            return f'{self.lhs} -> {rhs} ({self.prec})'
        return f'{self.lhs} -> {rhs}'


class ItemSet:
    def __init__(self, grammar, items):
        self.items = set(items)

        # complete the itemset by repeatedly finding all of the productions
        # which come after pointers in the set, and adding all the rules that
        # produce them recursively.
        while True:
            old_size = len(self.items)
            nexts = set(
                s for s in chain.from_iterable(
                    r.next_symbols for r in self.items)
                if not s.is_terminal)
            self.items.update(
                grammar.rules[r].with_pointer(0)
                for r in grammar.find_rule_indices(nexts))
            if len(self.items) == old_size:
                break

    @property
    def next_symbols(self):
        """Gets a list of possible next symbols."""
        return set(chain.from_iterable(r.next_symbols for r in self.items))

    def advance(self, symbol):
        """Advances the itemset by the given symbol.

        Returns a frozenset of items where items which can be advanced by the
        given symbol have been, and items which cannot have been dropped.
        """
        return frozenset(
            item.advanced for item in self.items
            if symbol in item.next_symbols)

    @property
    def mode(self):
        """Gets the lexer mode for this itemset."""

        # A simple example of rules using lexer modes:
        #
        #     R -> n S z  (mode U)
        #     S -> x y    (mode V)
        #
        # where n is a mode-0 token and x, y, z are mode U tokens. In this
        # case, we want to accept n, shift to mode V, accept tokens x, y, z,
        # then shift back to mode U. The itemsets for the above rules are:
        #
        #  0. R -> . n S z
        #
        #  1. R -> n . S z
        #   + S -> . x y
        #
        #  2. S -> x . y
        #
        #  3. S -> x y .
        #
        #  4. R -> n S . z
        #
        #  5. R -> n S z .
        #
        # Clearly, in set 0 we want mode U so we can get n, shifting us to set
        # 1. The set stack is now [0, 1], and we want to be in mode V so we can
        # get x for our lookahead.
        #
        # Now we shift set 2, making our set stack [0, 1, 2]. We still want
        # mode V to get y. This lets us shift set 3, set stack [0, 1, 2, 3]. We
        # still want mode V, so we can get z.
        #
        # At this point, we reduce by S, which makes our set stack [0, 1, 4].
        # We don't get a new lookahead after a reduce, so we don't care about
        # the mode.
        #
        # Then we shift by 5, set stack [0, 1, 4, 5]. At this point, we need to
        # be back in mode U for whatever comes after R.
        #
        # From the above we can derive the following set-mode associations.
        # Pairs marked (I) indicates that the mode has the same mode as the
        # previous one on the stack (ignoring set 4, which doesn't really have
        # a mode):  0=U, 1=V, 2=V (I), 3=V (I), 5=U
        #
        # In sets 0 and 1, we're at position 0 in a rule with the appropriate
        # mode, so we assign the mode based on that. Set 2 can inherit. In set
        # 5, we're at the end of a rule with the appropriate mode. Assigning
        # based on that also assigns mode V to set 3, which is not necessary,
        # but harmless.
        #
        # Therefore, we only care about rules where the pointer is at the
        # beginning or end.
        modes = {r.mode for r in self.items
                 if r.pointer == 0 or len(r.next_symbols) == 0}

        # If there are no such rules, we can inherit. Note that we can't assign
        # based on the rule that we're in the middle of, because then we'd be
        # trying to assign mode U to set 1, which we're already assigning mode
        # V to.
        if len(modes) == 0:
            return Parser.INHERIT_MODE

        # If we end up with two rules giving us conflicting modes, we will
        # consider that an error in the grammar.
        assert len(modes) == 1, f"mode/mode conflict: {self.items}"
        return modes.pop()


@attr.s(slots=True, frozen=True, repr=False, cmp=False)
class Special:
    name = attr.ib()

    def __repr__(self):
        return "$" + self.name


class Grammar:
    EMPTY_TOKEN = Special("EMPTY")
    EMPTY = Symbol(EMPTY_TOKEN)
    END = Special("END")

    def __init__(self, start_symbol, end_symbols, rules):
        self.rules = rules
        self.start_symbol = _convert_lhs(start_symbol)
        self.end_symbols = frozenset(_convert_lhs(s) for s in end_symbols)

    @property
    def symbols(self):
        ts = set()
        for rule in self.rules:
            ts.add(rule.lhs)
            for syms in rule.rhs:
                ts.update(syms)
        return ts

    def find_rule_indices(self, symbols):
        """Returns a list of rule indices which produce the given symbols."""
        return [k for k, r in enumerate(self.rules) if r.lhs in symbols]

    def find_starting_rule_index(self):
        """Finds the starting rule given the start symbol."""
        starts = self.find_rule_indices([self.start_symbol])
        if len(starts) == 0:
            raise Exception('No starting rule found')
        elif len(starts) > 1:
            raise Exception('Multiple starting rules found')
        elif len(self.rules[starts[0]].rhs) != 1:
            raise Exception('Starting rule must have one token')
        else:
            return starts[0]

    def build_firstsets(self):
        """Builds the First sets for every extended symbol.

        The First set is the set of all terminals which can grammatically
        appear at the beginning of a given symbol.
        """

        start_time = time.perf_counter()
        firstsets = {}

        # pre-populate with empty firstsets (for nonterminals) and identity
        # firstsets (for terminals)
        for sym in self.symbols:
            if sym.is_terminal:
                firstsets[sym] = {sym.parent}
            else:
                firstsets[sym] = set()

        # 1. if V -> x, then First(V) contains x
        # 2. if V -> (), then First(V) contains ()
        nzrules = []
        for rule in self.rules:
            if len(rule.rhs) == 0:
                firstsets[rule.lhs].add(self.EMPTY)
                continue
            for sym in rule.rhs[0]:
                if sym.is_terminal:
                    firstsets[rule.lhs].update(firstsets[sym])
                else:
                    # cache rules that rule 3 applies to in advance
                    nzrules.append(rule)

        # 3. if V -> A B C, then First(V) contains First(A) - (). If First(A)
        #    contains (), then First(V) also contains First(B), etc. If A, B,
        #    and C all contain (), then First(V) contains ().
        #
        # Since rules can be (mutually) left-recursive, we may have to apply
        # this rule multiple times to catch everything.
        updated = True
        count = 0
        while updated:
            count += 1
            updated = False
            for rule in nzrules:
                # we know in advance that these rules begin with a nonterminal
                # on the right-hand side, because they're the ones we cached
                # when applied rules 1 & 2.
                old_len = len(firstsets[rule.lhs])
                for symbols in rule.rhs:
                    fs = frozenset(chain.from_iterable(
                        firstsets[s] for s in symbols))
                    if self.EMPTY not in fs:
                        firstsets[rule.lhs].update(fs)
                        break
                    firstsets[rule.lhs].update(fs - {self.EMPTY})
                else:
                    firstsets[rule.lhs].add(self.EMPTY)
                if len(firstsets[rule.lhs]) > old_len:
                    updated = True

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        logger.debug(__(
            "Built firstsets ({} cycles) in {:.2f}ms",
            count, elapsed_ms))
        return firstsets

    def build_followsets(self):
        """Builds the Follow sets for every extended symbol.

        The Follow set is the set of all terminals which can grammatically
        appear after the given symbol.
        """

        firstsets = self.build_firstsets()
        start_time = time.perf_counter()
        followsets = {}

        # pre-populate with empty followsets
        for sym in self.symbols:
            if sym == self.start_symbol:
                followsets[sym] = {s.parent for s in self.end_symbols}
            else:
                followsets[sym] = set()

        # suppose we have a rule R -> a*Db. Then we add First(b) to Follow(D).
        for rule in self.rules:
            for k in range(len(rule.rhs) - 1):
                for s in rule.rhs[k]:
                    if not s.is_terminal:
                        for t in rule.rhs[k+1]:
                            followsets[s].update(firstsets[t])

        # suppose we have a rule R -> a*D. Then we add Follow(R) to Follow(D).
        # Because we can end up with irritating things like two follow sets
        # mutually depending on each other, we've handled this by just applying
        # the rule until we reach a fixed state.
        updated = True
        count = 0
        while updated:
            count += 1
            updated = False
            for rule in self.rules:

                # empty rules don't tell us anything for this pass
                if len(rule.rhs) == 0:
                    continue

                for s in rule.rhs[-1]:
                    if not s.is_terminal:
                        old_len = len(followsets[s])
                        followsets[s].update(
                            followsets[rule.lhs])
                        if len(followsets[s]) > old_len:
                            updated = True

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        logger.debug(__(
            "Build followsets ({} cycles) in {:.2f}ms",
            count, elapsed_ms))
        return followsets

    def build_parser(self, hidden=None, channel=ReStream.CHANNEL_DEFAULT):
        logger.debug(__("Grammar has {} rules", len(self.rules)))

        start_time_t = time.perf_counter()
        translation_table = TranslationTable(self)
        extended_grammar = translation_table.build_extended_grammar()
        modes = translation_table.build_modes()
        followsets = extended_grammar.build_followsets()
        start_time = time.perf_counter()

        # Build the action/goto table. This is what the parse function actually
        # uses. In the action part of the table (where the input is a
        # terminal), there are two possible actions: shift, and reduce. These
        # are represented by an (action, index) tuple. In response to a reduce,
        # the parser will execute a goto by providing a nonterminal as input.
        # These are represented as integers.
        agtable = {}
        conflicts = []

        # copy the nonterminal entries in the translation table over as gotos
        # and the terminal entries as shifts.
        for (f, s), t in translation_table.items():
            if s.is_terminal:
                agtable[(f, s.value)] = ('shift', None, t)
            else:
                agtable[(f, s.value)] = t  # goto

        # construct the final sets by merging extended rules which are based on
        # the same rule and have the same end point.
        finalset_rules = [None] * len(translation_table.itemsets)
        finalset_followsets = [set() for _ in translation_table.itemsets]
        for rule in extended_grammar.rules:
            if len(rule.rhs) == 0:
                # if the rule has no rhs, then the starting point is the same
                # as the ending point.
                final = rule.lhs.start
            else:
                finals = {s.end for s in rule.rhs[-1]}
                assert len(finals) == 1
                final = finals.pop()
            if finalset_rules[final] is not None \
               and finalset_rules[final] != rule.parent:
                # This is a reduce/reduce conflict. We decide how to resolve
                # this based on the precedence of the rules involved.
                # TODO work out how to handle ties?
                # TODO check if this is sound. Somehow
                if finalset_rules[final].prec is None or \
                   rule.parent.prec is None or \
                   finalset_rules[final].prec == rule.parent.prec:
                    conflicts.append(
                        f'reduce/reduce:\n'
                        f'  {finalset_rules[final]}\n'
                        f'  {rule.parent}')
                    continue

                logging.debug(__(
                    "Resolved reduce/reduce conflict between {} and {}",
                    finalset_rules[final],
                    rule.parent))
                if finalset_rules[final].prec > rule.parent.prec:
                    continue

            finalset_rules[final] = rule.parent
            finalset_followsets[final].update(followsets[rule.lhs])

        # add the merged reductions to the table
        for k, followset in enumerate(finalset_followsets):
            for symbol in followset:
                if (k, symbol.value) in agtable:
                    # This is a shift/reduce conflict. We decide how to resolve
                    # this based on the precedence of the rules involved.

                    # Note that the shift index is a state number, not a rule
                    # number. State numbers correspond to item sets. In
                    # particular, we're looking for the rule that has already
                    # been partially applied.
                    _, _, shift_index = agtable[(k, symbol.value)]
                    partials = [
                        i for i
                        in translation_table.itemsets[shift_index].items
                        if i.pointer > 0]
                    assert len(partials) == 1, 'shift/reduce (GENERATOR BUG)'
                    shift_rule = partials[0]

                    # If one of them is missing a precedence, go ahead and
                    # hard-fail.
                    if shift_rule.prec is None \
                       or finalset_rules[k].prec is None:
                        conflicts.append(
                            f'shift/reduce:\n'
                            f'  {shift_rule}\n'
                            f'  {finalset_rules[k]}')
                        continue

                    # If the shifting rule is right-associative, then we should
                    # break ties in favour of the shift. Otherwise, in favour
                    # of the reduce. Note because we look at the shift rule's
                    # associativity for this decision, a right-associative rule
                    # will bind more tightly than a left-associative rule with
                    # the same precedence.
                    if (shift_rule.prec > finalset_rules[k].prec
                        or (shift_rule.rassoc
                            and shift_rule.prec == finalset_rules[k].prec)):
                        continue

                # Check to see if this is actually the accept state
                if finalset_rules[k].lhs == self.start_symbol \
                   and symbol in self.end_symbols:
                    agtable[(k, symbol.value)] = ('accept', None, None)
                else:
                    agtable[(k, symbol.value)] = (
                        'reduce',
                        finalset_rules[k].lhs.value,
                        len(finalset_rules[k].rhs))

        if len(conflicts) > 0:
            logger.critical('\n\n'.join(conflicts))
            assert False, "conflicts detected"

        # build the hidden-channel parsers
        hidden_parsers = {
            channel: aux_grammar.build_parser(channel=channel)
            for channel, aux_grammar in (hidden or {}).items()
        }

        parser = Parser(agtable, modes, hidden_parsers, channel)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        elapsed_t_ms = (end_time - start_time_t) * 1000
        logger.debug(__(
            "Built action/goto table ({} enties) in {:.2f}ms",
            len(agtable), elapsed_ms))
        logger.debug(__("Built parser in {:.2f}ms total", elapsed_t_ms))
        logger.debug(__(
            "Symbols: {}, States: {}",
            len(self.symbols), len(translation_table.itemsets)))
        return parser


class TranslationTable:
    """A table of itemset/state transitions."""

    def __init__(self, grammar):
        self.end_symbols = grammar.end_symbols
        self.translation_table = {}
        self.itemsets = []
        self.itemset_index = {}

        start_time = time.perf_counter()

        # The first item set is based around the start rule
        start = grammar.find_starting_rule_index()
        startitem = grammar.rules[start].with_pointer(0)
        self.itemsets.append(ItemSet(grammar, {startitem}))
        self.itemset_index[frozenset({startitem})] = 0

        # next, we work our way down the itemsets, advancing them using the
        # allowed productions. The resulting items are used to construct new
        # itemsets. We also build the translation table as we go
        current = 0
        while current < len(self.itemsets):
            for symbol in self.itemsets[current].next_symbols:
                key = self.itemsets[current].advance(symbol)
                if key in self.itemset_index:
                    itemset = self.itemset_index[key]
                else:
                    itemset = len(self.itemsets)
                    self.itemset_index[key] = itemset
                    self.itemsets.append(ItemSet(grammar, key))
                self.translation_table[(current, symbol)] = itemset
            current += 1

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        logger.debug(__("Built {} itemsets in {:.2f}ms", current, elapsed_ms))

    def items(self):
        return self.translation_table.items()

    def build_extended_grammar(self):
        """Builds the extended rule set.

        This produces a set of rules where each symbol sym has been replaced
        with the triple (s0, sym, s1) where s0 is the state/itemset preceding
        that symbol, and s1 is the state/itemset following it. If the rule can
        be applied from multiple states (i.e. it shows up in multiple
        itemsets), it will show up multiple times with different state numbers.
        """
        start_time = time.perf_counter()
        extended_rules = set()

        for current, itemset in enumerate(self.itemsets):
            rules_to_process = list(itemset.items)
            while len(rules_to_process) > 0:
                rule = rules_to_process.pop()
                if rule.pointer != 0:
                    continue
                prev = None
                state = current
                rhs = []
                abort = False
                parent = rule.parent
                if parent is None:
                    parent = rule
                for k, symbols in enumerate(rule.rhs):
                    prev = state
                    states = {self.translation_table[(state, s)]
                              for s in symbols}
                    if len(states) == 1:
                        state = states.pop()
                        rhs.append(tuple(
                            s.extend(prev, state) for s in symbols))
                        continue

                    # our alternation goes to different places, so split
                    # the rule, and try again.
                    for s in symbols:
                        rhs = list(rule.rhs)
                        rhs[k] = s
                        rules_to_process.append(
                            attr.evolve(rule, rhs=rhs, parent=rule))
                        abort = True
                    break
                if abort:
                    continue
                try:
                    lhs = rule.lhs.extend(
                        current, self.translation_table[(current, rule.lhs)])
                except KeyError:
                    lhs = rule.lhs.extend(current, Grammar.END)
                    start_symbol = lhs
                extended_rules.add(
                    attr.evolve(rule, lhs=lhs, rhs=rhs, pointer=None,
                                parent=parent.with_pointer(None)))

        extended_grammar = Grammar(
            start_symbol,
            [s.extend(None, None) for s in self.end_symbols],
            extended_rules)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        sz = len(extended_rules)
        logger.debug(__(
            "Built extended grammar ({} rules) in {:.2f}ms",
            sz, elapsed_ms))
        return extended_grammar

    def build_modes(self):
        """Builds the lexer mode table.

        Depending on what rule we are currently following, we ask the lexer to
        operate in different modes. Each itemset/state is associated with one
        mode, that of the rule(s) which are currently in-progress.
        """

        return [s.mode for s in self.itemsets]


class Parser:
    NORMAL_MODE = 0
    INHERIT_MODE = -1

    def __init__(self, agtable, modes, hidden, channel):
        self.agtable = agtable
        self.modes = modes
        self.hidden = hidden
        self.channel = channel

    def select_mode(self, set_stack):
        return next((self.modes[s]
                     for s in reversed(set_stack)
                     if self.modes[s] != self.INHERIT_MODE),
                    self.NORMAL_MODE)

    def next_token_skip_hidden(self, stream, next_token, set_stack):
        while True:
            lookahead = next_token(stream, self.select_mode(set_stack))
            if lookahead.channel == self.channel \
               or lookahead.channel == ReStream.CHANNEL_ALL:
                return lookahead

            # When a token comes in on a channel other than the one we're
            # handling, we delegate to another parser for that channel, which
            # consumes the input. This is useful for things like comments,
            # which can show up anywhere -- handling them in the main grammar
            # would be impossible.
            stream.rewind(lookahead)
            p = self.hidden[lookahead.channel]
            p(stream, next_token, lambda t, s, c, m: None)

    def __call__(self, stream, next_token, make_node):
        """Parses a given input.

        This method may be called multiple times and does not modify the
        object.

        'next_token' must be a callable which takes two arguments: the
        'stream', and an int for the mode, which is 0 initially. It must return
        a Token.

        'make_node' must be a callable, which is called every time a reduction
        is performed. It is passed three arguments: the nonterminal being
        reduced, a span covering the tokens involved in the reduction, and an
        iterable of the children of the reduction, which are a mix of Tokens
        and values returned from make_node.
        """

        start_time = time.perf_counter()
        output = []
        set_stack = [0]
        lookahead = self.next_token_skip_hidden(stream, next_token, set_stack)

        while True:
            try:
                action, sym, arg = self.agtable[(set_stack[-1], lookahead.t)]
            except KeyError:
                try:
                    action, sym, arg = self.agtable[
                        (set_stack[-1], Grammar.EMPTY_TOKEN)]
                    assert action == 'reduce'
                except KeyError:
                    msg = [f"Got {lookahead.t} but expected one of:"]
                    for state, token in self.agtable:
                        if state == set_stack[-1]:
                            msg.append(f"  {token}")
                    raise ParseError("\n".join(msg))

            if action == 'shift':
                output.append((lookahead, lookahead.span))
                set_stack.append(arg)
                lookahead = self.next_token_skip_hidden(
                    stream, next_token, set_stack)
            elif action == 'reduce':
                if arg > 0:
                    children, spans = zip(*output[-arg:])
                    span = TextSpan.cover(spans)
                    del output[-arg:]
                    del set_stack[-arg:]
                else:
                    children = []
                    # Since we are reducing an empty rule, we know by [vigorous
                    # handwaving] that the lack-of-tokens we're trying to
                    # reduce is bounded on the left by the last item in the
                    # output stack (if present) and on the right by the
                    # lookahead token. Note that this approach may result in
                    # the span corresponding to a block of whitespace or a
                    # comment.
                    end = lookahead.span.start
                    if len(output) > 0:
                        start = output[-1][1].end
                    else:
                        start = end
                    span = TextSpan(*start, *end)
                set_stack.append(self.agtable[(set_stack[-1], sym)])
                output.append((make_node(sym, span, children,
                                         self.modes[set_stack[-1]]),
                               span))
            else:
                assert action == 'accept'
                break

        assert len(output) == 1

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        if self.channel == ReStream.CHANNEL_DEFAULT:
            logger.debug(__(
                "Parsed input on channel {} in {:.2f}ms",
                self.channel, elapsed_ms))
        return output[0][0]
