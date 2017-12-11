from parserGenerator.units import *


packageName = "pythonGenerator"
className = "Grammar"

# Do it.
code = CodeGenerator()

# Header

code.addLine("package " + packageName + ";\n")
code.addLine("import at.searles.parsing.lexer.Lexer;")
code.addLine("import at.searles.parsing.lexer.TokStream;")
code.addLine("import at.searles.parsing.lexer.Token;")
code.addLine("import at.searles.parsing.lexer.TokenSet;")
code.addLine("import at.searles.parsing.regex.CharSet;")
code.addLine("import at.searles.parsing.regex.Regex;")

# Start class

code.beginBlock("public class " + className)

# Part 1: Functions to combine tokens

toNum = FuncUnit("toNum", ["CharSequence"], ["Integer"])
add = FuncUnit("add", ["Integer", "Integer"], ["Integer"])
sub = FuncUnit("sub", ["Integer", "Integer"], ["Integer"])
mul = FuncUnit("mul", ["Integer", "Integer"], ["Integer"])
div = FuncUnit("div", ["Integer", "Integer"], ["Integer"])
neg = FuncUnit("neg", ["Integer"], ["Integer"])

# Add declarations

toNum.setBody("return seq.charAt(0) - '0';")
add.setBody("return a + b;")
sub.setBody("return a - b;")
mul.setBody("return a * b;")
div.setBody("return a / b;")
neg.setBody("return -a;")

toNum.declare(code, ["seq"])
add.declare(code, ["a", "b"])
sub.declare(code, ["a", "b"])
mul.declare(code, ["a", "b"])
div.declare(code, ["a", "b"])
neg.declare(code, ["a"])

# Part 2: Define Tokens and lexers

lexer = Lexer("lexer")
ws = HiddenToken("ws", lexer, "CharSet.chars('\\n', ' ')")
plus = Token("plus", lexer, "\"+\"")
minus = Token("minus", lexer, "\"-\"")
times = Token("times", lexer, "\"*\"")
slash = Token("slash", lexer, "\"/\"")
open = Token("open", lexer, "\"(\"")
close = Token("close", lexer, "\")\"")
numTok = Token("num", lexer, "CharSet.interval('0', '9')")

# These will be declared as members
members = [ lexer, ws, plus, minus, times, slash, open, close, numTok ]

# Part 3: Define Parsers

sum = Parser("sum", [], ["Integer"])
product = Parser("product", [], ["Integer"])
negated = Parser("negated", [], ["Integer"])
term = Parser("term", [], ["Integer"])
num = TokenParser("num", numTok, toNum)

# These parsers will be added as methods
parsers = [sum, product, negated, term, num]

# Grammar rules

sum.setDefinition(
    product + (
        plus + product + add
        | minus + product + sub
        ).rep()
)

product.setDefinition(
    negated + (
        times + negated + mul
        | slash + negated + div
        ).rep()
)

negated.setDefinition(
    minus + negated + neg
    | term
)

term.setDefinition(
    num | open + sum + close
)


# Add declarations to code
for m in members:
    m.declare(code)

for p in parsers:
    p.declare(code, [], "stream")

# Error handling

code.beginBlock("private void parsingError(TokStream stream, String expected)")
code.addLine("throw new IllegalArgumentException(\"Expected \" + expected + \" at \" + stream);")
code.endBlock()

code.endBlock()

