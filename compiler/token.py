import enum

class Token(enum.Enum):
    unknown = -2
    eof = -1
    whitespace = 0
    word = 1
    numeric = 2
    left_paren = 3
    right_paren = 4
    left_bracket = 5
    right_bracket = 6
    left_brace = 7
    right_brace = 8
    double_quote = 9
    single_quote = 10
    operator = 11
    keyword = 12