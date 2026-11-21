"""Small exercises with complete answer sets derived from the stated rules."""

import json
import operator
import string
from itertools import combinations, combinations_with_replacement, permutations, product


PY = "https://docs.python.org/3.12/"
BITS = PY + "library/stdtypes.html#bitwise-operations-on-integer-types"
TEXT = "https://www.rfc-editor.org/rfc/rfc20.html"
JSON = "https://www.rfc-editor.org/rfc/rfc8259.html"
ALG = "https://algs4.cs.princeton.edu/"
SQL = "https://www.sqlite.org/lang_select.html"
IP = "https://www.rfc-editor.org/rfc/rfc4632.html"
UNIX = "https://pubs.opengroup.org/onlinepubs/9799919799/"


def practice(bank, answer_type):
    def question(slug, category, prompt, scope, values, source, common, *, root=None,
                 aliases=None, sensitive=False):
        bank.add(slug, category, prompt, scope,
                 (answer_type(str(value), source, aliases(value) if aliases else []) for value in values),
                 "Original question; rule or technical reference", common=common, root=root, sensitive=sensitive)

    def numbers(slug, category, prompt, scope, values, source, common, root=None):
        question(slug, category, prompt, scope, values, source, common, root=root)

    def csv_aliases(value):
        parts = value.split(",")
        return [", ".join(parts), " ".join(parts), "[" + value + "]", "[" + ", ".join(parts) + "]"]

    def csv(values):
        return ",".join(map(str, values))

    numbers("binary-four-bits", "Binary", "Give a four-bit binary number.",
            "Use exactly four digits. Leading zeroes count.", (f"{n:04b}" for n in range(16)), BITS,
            "0000|1111|0001|1010|1000", "1011")
    numbers("binary-two-ones", "Binary", "Give a six-bit number with exactly two 1s.",
            "Use a six-digit binary string. Leading zeroes count.",
            (f"{n:06b}" for n in range(64) if n.bit_count() == 2), BITS, "000011|110000|100001|001100")
    numbers("binary-odd", "Binary", "Give an odd number written in binary.",
            "Use exactly five binary digits. Leading zeroes count.",
            (f"{n:05b}" for n in range(1, 32, 2)), BITS, "00001|00011|11111|10101|10001")
    numbers("binary-palindrome", "Binary", "Give an eight-bit palindrome.",
            "Use eight binary digits. The string must read the same in both directions.",
            (f"{n:04b}" + f"{n:04b}"[::-1] for n in range(16)), BITS, "00000000|11111111|10000001|01111110")
    numbers("binary-third-bit", "Binary", "Give a byte with its lowest bit set and its highest bit clear.",
            "Use eight binary digits, with the most significant bit on the left.",
            (f"{n:08b}" for n in range(1, 128, 2)), BITS,
            "00000001|01111111|00000011|00000101|01010101")
    numbers("binary-shift", "Binary", "Give a number that can result from shifting a four-bit value left once.",
            "Give the decimal result. Keep the new high bit instead of truncating it.",
            range(0, 32, 2), BITS, "0|2|4|8|16|30")
    question("hex-byte", "Hexadecimal", "Give a byte in hexadecimal.",
             "Use exactly two hexadecimal digits, with or without an 0x prefix.",
             (f"{n:02X}" for n in range(256)), BITS, "00|FF|01|0A|10|AA|80",
             root="C7", aliases=lambda n: ["0x" + n])
    question("hex-repeated", "Hexadecimal", "Give a two-digit hex value with both digits the same.",
             "Type two hex digits. A leading 0x is optional.",
             (n * 2 for n in string.digits + "ABCDEF"), BITS, "00|11|FF|AA|22",
             aliases=lambda n: ["0x" + n])
    question("hex-color", "CSS", "Give a hex color with full red and zero green.",
             "Use a six-digit RGB color. The blue channel can be anything.",
             (f"#FF00{n:02X}" for n in range(256)), "https://drafts.csswg.org/css-color-4/#hex-notation",
             "#FF0000|#FF00FF|#FF0080|#FF0001|#FF007F", aliases=lambda n: [n[1:]])
    numbers("signed-byte", "Data representation", "Give an integer that fits in a signed byte.",
            "Use decimal. A signed byte uses 8-bit two’s complement.", range(-128, 128), BITS,
            "0|1|-1|127|-128|10|100")
    numbers("unsigned-only", "Data representation", "Give a number that fits in an unsigned byte but overflows a signed byte.",
            "Use a decimal integer. Both byte types are eight bits.", range(128, 256), BITS,
            "128|255|200|129|254")
    numbers("ascii-letter-codes", "Text and encoding", "Give the ASCII code for an English letter.",
            "Use the decimal ASCII code for an uppercase or lowercase letter.", map(ord, string.ascii_letters),
            TEXT, "65|97|66|98|90|122")
    numbers("ascii-control-codes", "Text and encoding", "Give a decimal code for an ASCII control character.",
            "Use the ASCII control-code range, including DEL. Printable characters are separate.",
            [*range(32), 127], TEXT, "0|9|10|13|27|127")
    punctuation = {
        "!": "exclamation mark", '"': "double quote", "#": "hash|number sign", "$": "dollar sign",
        "%": "percent sign", "&": "ampersand", "'": "apostrophe|single quote", "(": "open parenthesis",
        ")": "close parenthesis", "*": "asterisk", "+": "plus sign", ",": "comma", "-": "hyphen|minus sign",
        ".": "period|full stop|dot", "/": "slash|forward slash", ":": "colon", ";": "semicolon",
        "<": "less-than sign", "=": "equals sign", ">": "greater-than sign", "?": "question mark",
        "@": "at sign", "[": "open square bracket", "\\": "backslash", "]": "close square bracket",
        "^": "caret", "_": "underscore", "`": "backtick", "{": "open brace", "|": "pipe|vertical bar",
        "}": "close brace", "~": "tilde", "space": "space character",
    }
    question("ascii-symbols", "Text and encoding", "Name or type a printable ASCII character that isn’t a letter or digit.",
             "A symbol or its common name works. Type space for the space character.", punctuation,
             TEXT, ".|,|!|?|@|#|+|-|space", root="~", aliases=lambda n: punctuation[n].split("|"))
    question("letter-unicode-escape", "Text and encoding", "Give a Unicode escape for an English letter.",
             "Use a four-digit Python Unicode escape of the form \\uXXXX. Give the escape text without quotes.",
             (f"\\u{ord(c):04x}" for c in string.ascii_letters),
             PY + "reference/lexical_analysis.html#escape-sequences",
             "\\u0041|\\u0061|\\u0042|\\u0062", sensitive=True,
             aliases=lambda n: [n[:2] + n[2:].upper()])
    question("reg-ex-pair", "Regular expressions", "Give a string that matches the regex [a-z][0-9].",
             "Match the entire string. Use one lowercase ASCII letter followed by one digit.",
             (c + n for c, n in product(string.ascii_lowercase, string.digits)), PY + "library/re.html",
             "a0|a1|z9|x1|b2|a9", sensitive=True)
    question("regex-letter-range", "Regular expressions", "Give a string that matches the regex [a-f]{2}.",
             "Match the entire string using exactly two lowercase letters in the given range.",
             (a + b for a, b in product("abcdef", repeat=2)), PY + "library/re.html",
             "aa|ab|ff|af|bc|ee", sensitive=True)
    question("regex-optional", "Regular expressions", "Give a string that matches the regex [a-z]?[0-9].",
             "Match the whole string. The letter is optional.",
             (*string.digits, *(a + b for a, b in product(string.ascii_lowercase, string.digits))),
             PY + "library/re.html", "0|1|9|a1|a0|z9", sensitive=True)
    question("python-one-letter-name", "Python", "Give a one-letter variable name in Python.",
             "Use exactly one ASCII letter. Uppercase and lowercase are different names.", string.ascii_letters,
             PY + "reference/lexical_analysis.html#identifiers", "x|i|j|n|a|y|z|T", sensitive=True)
    numbers("decimal-palindromes", "Algorithms", "Give a three-digit palindrome.",
            "Use a decimal number with no leading zero. It must read the same backward and forward.",
            (100 * a + 10 * b + a for a, b in product(range(1, 10), range(10))),
            ALG + "53substring/", "101|111|121|999|202")
    question("balanced-parentheses", "Stacks and queues", "Give a balanced string of four pairs of parentheses.",
             "Type only parentheses. No prefix can close more pairs than it opens.",
             (value for chars in product("()", repeat=8) if balanced(value := "".join(chars))),
             ALG + "13stacks/", "()()()()|(((())))|(())(())|(()())()", root="(()(()))")
    numbers("array-indices", "Arrays and lists", "Give a valid index into an array of 16 elements.",
            "Use zero-based indexing. Give one nonnegative integer.", range(16),
            PY + "library/stdtypes.html#common-sequence-operations", "0|1|15|2|8")
    numbers("negative-indices", "Arrays and lists", "Give a valid negative index into a Python list with 16 items.",
            "Use one negative index. Python counts negative indices from the end.", range(-16, 0),
            PY + "library/stdtypes.html#common-sequence-operations", "-1|-2|-16|-3|-8")
    question("sorted-list", "Arrays and lists", "Give three numbers already sorted from smallest to largest.",
             "Choose all three from 0–3. Repeats are allowed. Separate your numbers with commas.",
             map(csv, combinations_with_replacement(range(4), 3)), ALG + "21elementary/", "0,1,2|1,2,3|0,0,0|3,3,3",
             aliases=csv_aliases)
    question("list-repeated-value", "Arrays and lists", "Give a three-item list that contains a duplicate.",
             "Choose each item from 0–3. Separate your numbers with commas.",
             (csv(values) for values in product(range(4), repeat=3) if len(set(values)) < 3),
             PY + "tutorial/datastructures.html", "0,0,0|1,1,2|0,0,1|1,2,1|3,3,3", aliases=csv_aliases)
    question("permutations", "Algorithms", "Give a different ordering of the numbers 1, 2, 3 and 4.",
             "Use each number once. The original order is excluded. Separate your numbers with commas.",
             (csv(values) for values in permutations(range(1, 5)) if values != (1, 2, 3, 4)),
             ALG, "4,3,2,1|2,1,3,4|1,2,4,3|3,4,1,2", aliases=csv_aliases)
    question("python-slices", "Arrays and lists", "Give a Python slice that picks at least one item from an eight-item list.",
             "Type start:stop with 0 ≤ start < stop ≤ 8. Square brackets are optional.",
             (f"{start}:{stop}" for start in range(8) for stop in range(start + 1, 9)),
             PY + "library/stdtypes.html#common-sequence-operations", "0:8|0:1|1:2|7:8|0:4",
             aliases=lambda value: ["[" + value + "]"])
    question("stack-pop", "Stacks and queues", "Give a possible pop order for a stack.",
             "Push 1, 2, 3, 4 in that order. You may pop between pushes. Give the four popped values in order.",
             map(csv, pop_orders((), (), 1)), ALG + "13stacks/", "4,3,2,1|1,2,3,4|2,1,4,3|3,2,1,4",
             aliases=csv_aliases)
    question("queue-snapshot", "Stacks and queues", "Give a possible snapshot of a FIFO queue.",
             "A through H arrive in order. Some may have left and others may not have arrived. List the nonempty queue from front to back.",
             (csv("ABCDEFGH"[start:stop]) for start in range(8) for stop in range(start + 1, 9)),
             ALG + "13stacks/", "A|H|A,B|F,G,H|A,B,C,D,E,F,G,H", aliases=csv_aliases)
    numbers("tree-size", "Trees and graphs", "How many nodes could a binary tree of height four have?",
            "Height is the number of edges on the longest root-to-leaf path. Give one possible count.",
            range(5, 32), ALG + "32bst/", "5|31|15|16|8")
    numbers("tree-edges", "Trees and graphs", "Give a possible edge count for a tree with at most 20 nodes.",
            "The tree has at least one node. Give only the number of edges.",
            range(20), ALG + "41graph/", "0|1|2|19|10")
    question("star-bfs", "Trees and graphs", "Give a breadth-first traversal starting at A.",
             "A is the center of a star connected to B, C, D, and E. Visit every node once. Neighbors can be visited in any order.",
             (csv(("A", *p)) for p in permutations("BCDE")), ALG + "41graph/",
             "A,B,C,D,E|A,E,D,C,B|A,C,B,D,E|A,B,D,C,E", aliases=csv_aliases)
    numbers("graph-degree", "Trees and graphs", "Give a possible degree for one vertex in an undirected graph with 16 vertices.",
            "The graph is simple, so no loops or repeated edges are allowed. Give one nonnegative degree.",
            range(16), ALG + "41graph/", "0|1|2|15|3")
    numbers("binary-search-lengths", "Algorithms", "Give a list size binary search can handle in at most four checks.",
            "Use a nonempty sorted list. Count each inspected midpoint as one check, even when the target is missing.",
            range(1, 16), ALG + "11model/BinarySearch.java.html", "1|2|4|8|15")
    question("bubble-swap", "Algorithms", "Give two adjacent values that bubble sort would swap.",
             "Sort in ascending order. Use two different integers from 1–8 in the order they appear.",
             (csv((left, right)) for left in range(1, 9) for right in range(1, left)),
             ALG + "21elementary/", "2,1|8,1|3,2|8,7|4,2", aliases=csv_aliases)
    costs = [
        ("", "Time complexity", "Give a function that runs in O(n²) time.",
         "Use one monomial c·n^k with c from 1 to 10 and k equal to 0, 1, or 2. Give the function without O( ).",
         range(3), "1|n|n^2|2n|2n^2"),
        ("-superlinear", "Time complexity", "Give a function that grows faster than n and no faster than n³.",
         "Use one monomial c·n^k with c from 1 to 10. Give the function without O( ).",
         (2, 3), "n^2|n^3|2n^2|2n^3"),
    ]
    for suffix, category, prompt, scope, exponents, common in costs:
        terms = {}
        for exponent in exponents:
            for coefficient in range(1, 11):
                part = "" if exponent == 0 else ("n" if exponent == 1 else f"n^{exponent}")
                value = part if coefficient == 1 and part else str(coefficient) + part
                terms[value] = [f"{coefficient}*{part}", f"{coefficient} * {part}"] if part else []
                if part:
                    terms[value].append(f"{coefficient}n" + ("" if exponent == 1 else ("²" if exponent == 2 else "³")))
        question("complexity" + suffix, category, prompt, scope, terms, ALG + "14analysis/", common,
                 aliases=terms.get)
    def json_character_aliases(value):
        char = json.loads(value)
        code = f"{ord(char):04x}"
        aliases = ['"\\u' + code + '"', '"\\u' + code.upper() + '"']
        if char == "/":
            aliases.append('"\\/"')
        return aliases

    question("json-one-character", "JSON", "Give a JSON string containing one printable ASCII character.",
             "Include the double quotes. Escape a quote or backslash if you use one.",
             (json.dumps(chr(n)) for n in range(32, 127)), JSON, '"a"|"A"|"x"|"1"|"0"|"?"',
             aliases=json_character_aliases, sensitive=True)
    numbers("json-integer", "JSON", "Give a valid integer value in JSON.",
            "Use a whole number from −20 to 20 as you would write it in JSON.", range(-20, 21),
            JSON, "0|1|-1|10|20|-20")
    properties = ["enabled", "active", "visible", "debug", "online", "verified", "darkMode", "readOnly"]
    booleans = {}
    for key, value in product(properties, (True, False)):
        compact = json.dumps({key: value}, separators=(",", ":"))
        name, literal = json.dumps(key), json.dumps(value)
        booleans[compact] = [
            f"{{{left}{name}{before}:{after}{literal}{right}}}"
            for left, before, after, right in product(("", " "), repeat=4)
        ]
    question("json-boolean-field", "JSON", "Give a one-field JSON object with a Boolean value.",
             "Choose a key from enabled, active, visible, debug, online, verified, darkMode, or readOnly.",
             booleans, JSON, '{"enabled":true}|{"active":false}|{"debug":true}', aliases=booleans.get, sensitive=True)
    question("sql-where", "SQL", "Give a comparison that can go in a SQL WHERE clause.",
             "Use the column age, one of =, <>, <, <=, >, >=, and an integer from 0–9. Skip WHERE.",
             (f"age {op} {n}" for op, n in product(("=", "<>", "<", "<=", ">", ">="), range(10))),
             "https://www.sqlite.org/lang_expr.html", "age = 0|age > 3|age < 9|age >= 1|age = 5",
             aliases=lambda value: ["WHERE " + value, value.replace(" ", "")])
    columns = ("id", "name", "email", "price", "stock", "rating")
    sorts = {
        f"ORDER BY {column} {direction}": [f"ORDER BY {column}"] if direction == "ASC" else []
        for column, direction in product(columns, ("ASC", "DESC"))
    }
    question("sql-order-by", "SQL", "Give a SQL clause that sorts results.",
             "Use ORDER BY and one column from id, name, email, price, stock, or rating. Either direction works.",
             sorts, SQL, "ORDER BY id ASC|ORDER BY name ASC|ORDER BY price DESC", aliases=sorts.get)
    projections = {f"SELECT {a}, {b}": [f"SELECT {a},{b}"] for a, b in permutations(columns, 2)}
    question("sql-select", "SQL", "Write the SELECT part of a query that returns two different columns.",
             "Choose from id, name, email, price, stock, and rating. Skip the FROM clause.",
             projections, SQL, "SELECT id, name|SELECT name, email|SELECT price, stock", aliases=projections.get)
    question("unix-mode", "Command line", "Give a valid three-digit Unix file permission.",
             "Type the octal mode, with or without a 0o prefix. Use three permission digits.",
             map("".join, product("01234567", repeat=3)), UNIX + "utilities/chmod.html",
             "644|755|777|600|700|664|000|666", aliases=lambda value: ["0o" + value])
    numbers("unix-exit-status", "Command line", "Give a possible shell exit status.",
            "Use the low eight bits of the exit code, written in decimal.",
            range(256), UNIX + "utilities/V3_chap02.html#exit", "0|1|2|126|127|130|255")
    question("ipv4-prefix-length", "Networking", "Give a valid IPv4 CIDR prefix length.",
             "Type the number of network bits. The leading slash is optional.", range(33), IP,
             "24|16|8|32|0|30", aliases=lambda n: [f"/{n}"])
    numbers("home-network-ip", "Networking", "Give an address you could assign to a device on 192.168.1.0/24.",
            "Give the full IPv4 address. Exclude the network and broadcast addresses.",
            (f"192.168.1.{n}" for n in range(1, 255)), IP,
            "192.168.1.1|192.168.1.2|192.168.1.10|192.168.1.100|192.168.1.254")
    numbers("small-subnet-ip", "Networking", "Give a usable host address in 10.0.0.0/28.",
            "Give the full IPv4 address. Exclude the network and broadcast addresses.",
            (f"10.0.0.{n}" for n in range(1, 15)), IP, "10.0.0.1|10.0.0.2|10.0.0.14|10.0.0.8")
    question("ipv6-hextet", "Networking", "Give a valid four-digit group from an IPv6 address.",
             "Use one group with exactly four hex digits and at least three zeroes.",
             sorted({"".join(values) for values in product("0123456789abcdef", repeat=4) if values.count("0") >= 3}),
             "https://www.rfc-editor.org/rfc/rfc4291.html", "0000|0001|000a|1000|000f")
    question("function-keys", "Computer systems", "Name a function key on a standard PC keyboard.",
             "Use the standard F1 through F12 key row.", (f"F{n}" for n in range(1, 13)),
             "https://www.w3.org/TR/uievents-key/#keys-function", "F1|F5|F12", root="F11")
    modifiers = ("Ctrl", "Shift", "Alt", "Meta")
    combos = {}
    for size in range(1, 5):
        for group in combinations(modifiers, size):
            value = "+".join(group)
            combos[value] = [form for order in permutations(group)
                             for form in ("+".join(order), " + ".join(order)) if form != value]
    question("keyboard-modifiers", "Computer systems", "Give a set of modifier keys you can hold while pressing another key.",
             "Choose any nonempty set from Ctrl, Shift, Alt, and Meta. Use + between multiple keys. Order is ignored.",
             combos, "https://www.w3.org/TR/uievents-key/#keys-modifier", "Ctrl|Shift|Alt|Ctrl+Shift",
             aliases=combos.get)
    operations = {"+": operator.add, "-": operator.sub, "*": operator.mul, "//": operator.floordiv}
    expressions = []
    for left, (op, calculate), right in product(range(21), operations.items(), range(21)):
        if (op != "//" or right != 0) and calculate(left, right) == 12:
            expressions.append(f"{left} {op} {right}")
    question("python-twelve", "Expressions", "Give a Python expression that evaluates to 12.",
             "Use two integers from 0–20 and exactly one of +, -, *, or //.",
             expressions, PY + "reference/expressions.html", "6 + 6|3 * 4|12 + 0|20 - 8|2 * 6",
             aliases=lambda value: [value.replace(" ", "")])
    question("remainder-one", "Expressions", "Give a modulo expression whose result is 1.",
             "Use a % b with a and b both from 1–16. Use a positive divisor.",
             (f"{a} % {b}" for a, b in product(range(1, 17), repeat=2) if a % b == 1),
             PY + "reference/expressions.html", "5 % 2|7 % 3|3 % 2|4 % 3|1 % 2",
             aliases=lambda value: [value.replace(" ", "")])
    question("python-true", "Expressions", "Give a Python comparison that evaluates to True.",
             "Use two integers from 0–3 and exactly one of ==, !=, <, <=, >, or >=.",
             (f"{a} {op} {b}" for a, (op, compare), b in product(
                range(4), (("==", operator.eq), ("!=", operator.ne), ("<", operator.lt),
                           ("<=", operator.le), (">", operator.gt), (">=", operator.ge)), range(4)) if compare(a, b)),
             PY + "reference/expressions.html#comparisons", "1 < 2|1 == 1|3 > 0|0 != 1",
             aliases=lambda value: [value.replace(" ", "")])


def balanced(value):
    opened = 0
    for token in value:
        opened += 1 if token == "(" else -1
        if opened < 0:
            return False
    return opened == 0


def pop_orders(stack, output, next_push):
    if len(output) == 4:
        yield output
        return
    if next_push <= 4:
        yield from pop_orders((*stack, next_push), output, next_push + 1)
    if stack:
        yield from pop_orders(stack[:-1], (*output, stack[-1]), next_push)
