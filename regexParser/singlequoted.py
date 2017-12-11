from parserGenerator.units import *

packageName = "pythonGenerator"
className = "SingleQuotedGrammar"

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

lexer = Lexer("lexer").declare(code)

closequote = Token("closeQuote", lexer, '"\'"').declare(code)
escapedChars = Token("escaped", lexer, 'Regex.text("\\\\\\\\").or(Regex.text("\\\\\\\'"))').declare(code)
allChars = Token("allChars", lexer, 'CharSet.all()').declare(code)

appendEscaped = FuncUnit("appendEscaped", ["StringBuilder", "CharSequence"], ["StringBuilder"])
appendEscaped.setBody("return sb.append(seq.charAt(1));")
appendEscaped.declare(code, ["sb", "seq"])

appendNormal = FuncUnit("appendNormal", ["StringBuilder", "CharSequence"], ["StringBuilder"])
appendNormal.setBody("return sb.append(seq.charAt(0));")
appendNormal.declare(code, ["sb", "seq"])

string = Parser("string", ["StringBuilder"], ["StringBuilder"])

chr = TokenParser("normalChars", allChars, appendNormal).declare(code, ["sb"], "stream")
esc = TokenParser("escapedChars", escapedChars, appendEscaped).declare(code, ["sb"], "stream")

# Grammar rules

string.setDefinition(closequote + Pass(["StringBuilder"]) | (esc | chr) + string).declare(code, ["sb"], "stream")

# Error handling

code.beginBlock("private void parsingError(TokStream stream, String expected)")
code.addLine("throw new IllegalArgumentException(\"Expected \" + expected + \" at \" + stream);")
code.endBlock()

code.endBlock()

