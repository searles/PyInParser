from parserGenerator.generator import CodeGenerator
from parserGenerator.units import *


packageName = "pythonGenerator"
className = "CharSetGrammar"

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

# Lexer for charsets

lexer = Lexer("lexer").declare(code)

# not allowed characters inside '[..]' are ]

# set = '^' decl | decl       invert
# decl = range (']' | decl)
# interval = chr ( '-' chr )?    interval
# chr = '\' esc | .
# esc = 'xNN' | 'uXXXX' | .   escaped

hat = Token("hat", lexer, '"^"').declare(code)
closebar = Token("closeBar", lexer, '"]"').declare(code)
to = Token("to", lexer, '"-"').declare(code)
backslash = Token("backslash", lexer, '"\\\\"').declare(code)
allChars = Token("allChars", lexer, 'CharSet.all()').declare(code)
escapedChars = Token("escapedChars", lexer,
                'CharSet.chars(\'x\').then(CharSet.interval(\'0\', \'9\').count(2))'
                '.or(CharSet.chars(\'u\').then(CharSet.interval(\'0\', \'9\').count(4)))'
                '.or(CharSet.all())').declare(code)

invert = FuncUnit("invert", ["CharSet"], ["CharSet"])
invert.setBody("return set.invert();")
invert.declare(code, ["set"])

add = FuncUnit("add", ["CharSet", "CharSet"], ["CharSet"])
add.setBody("return set0.union(set1);")
add.declare(code, ["set0", "set1"])

escaped = FuncUnit("escaped", ["CharSequence"], ["Character"])
escaped.setBody("switch(seq.charAt(0)) {\n"
                "case 'x': return (char) ((seq.charAt(1) - '0') * 16 + seq.charAt(2) - '0');\n"
                "case 'u': return (char) ((seq.charAt(1) - '0') * 4096 + (seq.charAt(2) - '0') * 256 + (seq.charAt(3) - '0') * 16 + seq.charAt(4) - '0');\n"
                "case 'n': return '\\n';\n"
                "case 'r': return '\\r';\n"
                "case 't': return '\\t';\n"
                "default: return seq.charAt(0);\n"
                "}")

escaped.declare(code, ["seq"])

normal = FuncUnit("normal", ["CharSequence"], ["Character"])
normal.setBody("return seq.charAt(0);")
normal.declare(code, ["seq"])

intervalSet = FuncUnit("intervalSet", ["Character", "Character"], ["CharSet"])
intervalSet.setBody("return CharSet.interval(ch0, ch1);")
intervalSet.declare(code, ["ch0", "ch1"])

singleSet = FuncUnit("singleSet", ["Character"], ["CharSet"])
singleSet.setBody("return CharSet.chars(ch);")
singleSet.declare(code, ["ch"])

# These will be declared as members

# Part 3: Define Parsers
# set = '^' decl | decl       invert
# decl = interval (']' | decl)
# interval = chr ( '-' chr )?    interval
# chr = '\' esc | .
# esc = 'xNN' | 'uXXXX' | .   escaped

set = Parser("charSet", ["CharSet"], ["Regex"])
decl = Parser("appendSet", ["CharSet"], ["CharSet"])
interval = Parser("interval", [], ["CharSet"])
chars = Parser("chr", [], ["Character"])

chr = TokenParser("chars", allChars, normal).declare(code, [], "stream")
esc = TokenParser("escapedChars", escapedChars, escaped).declare(code, [], "stream")

# Grammar rules

set.setDefinition(hat + decl + invert | decl).declare(code, ["set"], "stream")
decl.setDefinition(interval + add + (closebar + Pass(["CharSet"]) | decl)).declare(code, ["set"], "stream")
interval.setDefinition(chr + (to + chr + intervalSet | singleSet)).declare(code, [], "stream")
chars.setDefinition(backslash + esc | chr).declare(code, [], "stream")


# Error handling

code.beginBlock("private void parsingError(TokStream stream, String expected)")
code.addLine("throw new IllegalArgumentException(\"Expected \" + expected + \" at \" + stream);")
code.endBlock()

code.endBlock()

