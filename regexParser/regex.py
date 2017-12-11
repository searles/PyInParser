from parserGenerator.generator import CodeGenerator
from parserGenerator.units import *


packageName = "pythonGenerator"
className = "RegexGrammar"

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

singleQuotedGrammar = Object("singleQuotedGrammar", "SingleQuotedGrammar").declare(code)
quotedGrammar = Object("quotedGrammar", "QuotedGrammar").declare(code)
charSetGrammar = Object("charSetGrammar", "CharSetGrammar").declare(code)

singleQuote = singleQuotedGrammar.externCall("string", ["StringBuilder"], "StringBuilder", True)
quote = quotedGrammar.externCall("string", ["StringBuilder"], "StringBuilder", True)
charSet = charSetGrammar.externCall("set", ["CharSet"], "Regex", True)

lexer = Lexer("lexer").declare(code)

ws = HiddenToken("ws", lexer, "CharSet.chars('\\n', ' ')").declare(code)

numTok = Token("num", lexer,
               "CharSet.chars('0').or(CharSet.interval('1', '9').then(CharSet.interval('0', '9').range(0, 5)))").declare(code)
orTok = Token("orTok", lexer, '"|"').declare(code)
open = Token("open", lexer, '"("').declare(code)
close = Token("close", lexer, '")"').declare(code)
openCur = Token("openCur", lexer, '"{"').declare(code)
comma = Token("comma", lexer, '","').declare(code)
closeCur = Token("closeCur", lexer, '"}"').declare(code)
plusTok = Token("plus", lexer, '"+"').declare(code)
repTok = Token("rep", lexer, '"*"').declare(code)
optTok = Token("opt", lexer, '"?"').declare(code)
eagerTok = Token("eager", lexer, '"!"').declare(code)
dotTok = Token("dot", lexer, '"."').declare(code)

openBra = Token("openBra", lexer, '"["').declare(code)
openSingleQuote = Token("openSingleQute", lexer, '"\'"').declare(code)
openQuote = Token("openQuote", lexer, '"\\""').declare(code)

toNum = FuncUnit("toNum", ["CharSequence"], ["Integer"])
toNum.setBody("int n = 0;\n"
              "for(int i = 0; i < seq.length(); ++i) {\n"
              "    n = n * 10 + seq.charAt(i) - '0';\n"
              "}\n"
              "\n"
              "return n;")
toNum.declare(code, ["seq"])

num = TokenParser("num", numTok, toNum).declare(code, [], "streamVar")

orFn = FuncUnit("or", ["Regex", "Regex"], ["Regex"])
orFn.setBody("return regex0.or(regex1);")
orFn.declare(code, ["regex0", "regex1"])

concatFn = FuncUnit("concat", ["Regex", "Regex"], ["Regex"])
concatFn.setBody("return regex0.then(regex1);")
concatFn.declare(code, ["regex0", "regex1"])

repFn = FuncUnit("rep", ["Regex"], ["Regex"])
repFn.setBody("return regex.rep();")
repFn.declare(code, ["regex"])

optFn = FuncUnit("opt", ["Regex"], ["Regex"])
optFn.setBody("return regex.opt();")
optFn.declare(code, ["regex"])

plusFn = FuncUnit("plus", ["Regex"], ["Regex"])
plusFn.setBody("return regex.plus();")
plusFn.declare(code, ["regex"])

nonGreedyFn = FuncUnit("nonGreedy", ["Regex"], ["Regex"])
nonGreedyFn.setBody("return regex.nonGreedy();")
nonGreedyFn.declare(code, ["regex"])

rangeFn = FuncUnit("range", ["Regex", "Integer", "Integer"], ["Regex"])
rangeFn.setBody("return regex.range(from, to);")
rangeFn.declare(code, ["regex", "from", "to"])

minFn = FuncUnit("min", ["Regex", "Integer"], ["Regex"])
minFn.setBody("return regex.min(min);")
minFn.declare(code, ["regex", "min"])

countFn = FuncUnit("count", ["Regex", "Integer"], ["Regex"])
countFn.setBody("return regex.count(count);")
countFn.declare(code, ["regex", "count"])

textToRegexFn = FuncUnit("textToRegex", ["StringBuilder"], ["Regex"])
textToRegexFn.setBody("return Regex.text(sb.toString());")
textToRegexFn.declare(code, ["sb"])

# Part 3: Define Parsers

regex = Parser("regex", [], ["Regex"])
concat = Parser("concat", [], ["Regex"])
qualified = Parser("qualified", [], ["Regex"])
term = Parser("term", [], ["Regex"])

# Grammar rules

regex.setDefinition(
    concat + (orTok + concat + orFn).rep()
).declare(code, [], "stream")

concat.setDefinition(
    qualified + (qualified + concatFn).rep()
).declare(code, [], "stream")

qualified.setDefinition(
    term + (
            repTok + repFn |
            plusTok + plusFn |
            optTok + optFn |
            eagerTok + nonGreedyFn |
            openCur + num + (
                comma + (num + rangeFn | minFn)
                | countFn
            ) + closeCur
    ).rep()
).declare(code, [], "stream")

term.setDefinition(
    openBra + Expr("CharSet.empty", [], ["CharSet"], False) + charSet |
    openQuote + Expr("new StringBuilder", [], ["StringBuilder"], False) + quote + textToRegexFn |
    openSingleQuote + Expr("new StringBuilder", [], ["StringBuilder"], False) + singleQuote + textToRegexFn |
    dotTok + Expr("CharSet.all", [], ["Regex"], False) |
    open + regex + close
).declare(code, [], "stream")

# Error handling

code.beginBlock("private void parsingError(TokStream stream, String expected)")
code.addLine("throw new IllegalArgumentException(\"Expected \" + expected + \" at \" + stream);")
code.endBlock()

code.endBlock()

