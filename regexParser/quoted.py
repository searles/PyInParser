from parserGenerator.generator import CodeGenerator
from parserGenerator.units import *


packageName = "pythonGenerator"
className = "QuotedGrammar"

# Do it.
code = CodeGenerator()

# Header

code.addLine("package " + packageName + ";\n")
code.addLine("import at.searles.parsing.lexer.Lexer;")
code.addLine("import at.searles.parsing.lexer.TokStream;")
code.addLine("import at.searles.parsing.lexer.Token;")
code.addLine("import at.searles.parsing.regex.CharSet;")
code.addLine("import at.searles.parsing.regex.Regex;")

# Start class

code.beginBlock("public class " + className)

lexer = Lexer("lexer").declare(code)

closequote = Token("closeQuote", lexer, '"\\""').declare(code)
backslash = Token("backslash", lexer, '"\\\\"').declare(code)
allChars = Token("allChars", lexer, 'CharSet.all()').declare(code)
escapedChars = Token("escapedChars", lexer,
                     'CharSet.chars(\'x\').then(CharSet.interval(\'0\', \'9\').count(2))'
                     '.or(CharSet.chars(\'u\').then(CharSet.interval(\'0\', \'9\').count(4)))'
                     '.or(CharSet.all())').declare(code)

append = FuncUnit("append", ["StringBuilder", "Character"], ["StringBuilder"])
append.setBody("return sb.append(ch);")
append.declare(code, ["sb", "ch"])

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

string = Parser("string", ["StringBuilder"], ["StringBuilder"])
chars = Parser("chr", [], ["Character"])

chr = TokenParser("chars", allChars, normal).declare(code, [], "stream")
esc = TokenParser("escapedChars", escapedChars, escaped).declare(code, [], "stream")

# Grammar rules

string.setDefinition(closequote + Pass(["StringBuilder"]) | chars + append + string).declare(code, ["sb"], "stream")
chars.setDefinition(backslash + esc | chr).declare(code, [], "stream")


# Error handling

code.beginBlock("private void parsingError(TokStream stream, String expected)")
code.addLine("throw new IllegalArgumentException(\"Expected \" + expected + \" at \" + stream);")
code.endBlock()

code.endBlock()

