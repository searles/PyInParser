# global constant for the name of the boolean to check whether the parser succeeded.
statusVarName = "status"
tokenSequenceVarName = "seq"

class Unit:
    # @inputTypes Types of arguments (empty list if there are none)
    # @returnTypes Types of the return values. Functions and NamedUnits
    # are restricted to one.
    # @isParserUnit this boolean indicates whether a call to this unit
    #   can fail. In this case, the return value must be checked (if the
    #   returnType is None, this is a method returning a boolean instead of 'void')
    def __init__(self, inputTypes, returnTypes, isParserUnit):
        self.returnTypes = returnTypes
        self.inputTypes = inputTypes
        self.isParserUnit = isParserUnit

    def __or__(self, other):
        return Or(self, other)

    def __add__(self, next):
        return Then(self, next)

    def rep(self):
        return Rep(self)

    def opt(self):
        return Opt(self)

    # returns remaining inputArguments for the next function.
    def createCall(self, code, inputVars, streamVar):
        # last |inputTypes| elements are used
        localInputVars = inputVars[-len(self.inputTypes):] if self.inputTypes else []

        # create new variable for each returnType.
        returnVars = [code.createVar(t, None) for t in self.returnTypes]

        self.assignReturnVars(code, localInputVars, streamVar, returnVars)

        return inputVars[:len(inputVars) - len(self.inputTypes)] + returnVars

    # Calls this unit and writes the result into var.
    # input must be fully consumed.
    def assignReturnVars(self, code, inputVars, streamVar, returnVars):
        raise NotImplementedError()

################################################################################
## Subtypes of Unit ############################################################
################################################################################

class NamedUnit(Unit):
    def __init__(self, name, inputTypes, returnTypes, isParserUnit):

        if len(returnTypes) > 1:
            raise TypeError("NamedUnits must have at most 1 return type.")

        Unit.__init__(self, inputTypes, returnTypes, isParserUnit)
        self.name = name

    # Creates a declaration on class level. This can be a method definition
    # or an object creation. A subsequent call of 'call' should refer to this.
    # May return None if this unit refers to a different object (like EnvFunc)
    # @code code creator
    # @returnVar this is used for the argument in the inverse
    # @inArgs (possibly empty) list of strings that represent the names of the
    #   variables in which the arguments of a method call are stored. Should be null
    #   if not required for this type.
    # @stream name of TokStream that is used if this unit parses it (may be none if not used)
    #def declare(self, code, returnVar, inArgs, stream):
    #   raise NotImplemented();

    # Returns a string that represents a call of the element that is created/initiated
    # by a call to declare.
    # @inputVars arguments for a method call. May be none if not needed.
    # @streamVar Name of variable that contains the TokStream
    def call(self, inputVars, streamVar):
        if self.isParserUnit:
            argVars = inputVars + [streamVar]
        else:
            argVars = inputVars

        return self.name  + "(" + ", ".join(argVars) + ")"

    def assignReturnVars(self, code, inputVars, streamVar, returnVars):
        # returnVars is either empty or contains exactly one element.
        call = self.call(inputVars, streamVar) + ";"

        if not returnVars:
            if not self.isParserUnit:
                # void function
                code.addLine(call)
            else:
                # recognizer
                code.addLine(statusVarName + " = " + call)
        else:
            code.addLine(returnVars[0] + " = " + call)

            if self.isParserUnit:
                code.addLine(statusVarName + " = " + returnVars[0] + " != null;")


    def signature(self, inputVars, streamVar):
        returnType = self.returnTypes[0] if len(self.returnTypes) != 0 else \
            "boolean" if self.isParserUnit else "void"

        if self.isParserUnit:
            argTypes = self.inputTypes + ["TokStream"]
            argVars = inputVars + [streamVar]
        else:
            argTypes = self.inputTypes
            argVars = inputVars

        typedArgs = [" ".join(pair) for pair in zip(argTypes, argVars)]

        return "public " + returnType + " " + self.name + "(" + ", ".join(typedArgs) + ")"

    def __str__(self):
        return self.name

################################################################################
## Lexer and Tokens ############################################################
################################################################################

class Lexer:
    def __init__(self, name):
        self.name = name;

    def declare(self, code):
        code.addLine("private final Lexer " + self.name + " = new Lexer();")
        return self

class Object:
    def __init__(self, name, className):
        self.name = name
        self.className = className

    def declare(self, code):
        code.addLine("private final " + self.className + " " + self.name + " = new " + self.className + "();")
        return self

    def externCall(self, name, inputTypes, returnType, isParserUnit):
        return ExternFunction(self.name, name, inputTypes, returnType, isParserUnit)

class ExternFunction(NamedUnit):
    def __init__(self, qualifier, name, inputTypes, returnType, isParserUnit):
        NamedUnit.__init__(self, qualifier + "." + name, inputTypes, [returnType], isParserUnit)

class Expr(NamedUnit):
    def __init__(self, callCode, inputTypes, returnTypes, isParserUnit):
        NamedUnit.__init__(self, callCode, inputTypes, returnTypes, isParserUnit)

class HiddenToken:
    def __init__(self, name, lexer, regex):
        self.lexer = lexer
        self.name = name
        self.regex = regex

    def declare(self, code):
        code.addLine("public final Token " + self.name + " = " + self.lexer.name + ".hidden(" + self.regex + ");")
        return self

class Token(NamedUnit):
    def __init__(self, name, lexer, regex):
        NamedUnit.__init__(self, name, [], [], True)
        self.lexer = lexer
        self.name = name
        self.regex = regex

    def call(self, inputVars, stream):
        # This one has a special call.
        return self.name + ".recognizeToken(" + stream + ", null)"

    def declare(self, code):
        code.addLine("public final Token " + self.name + " = " + self.lexer.name + ".token(" + self.regex + ");")
        return self

class TokenParser(NamedUnit):
    def __init__(self, name, token, func):
        if not func.inputTypes or func.inputTypes[-1] != 'CharSequence':
            raise TypeError("last argument of func must be CharSequence")
        if func.isParserUnit:
            raise TypeError("func in TokenParser must not be a ParserUnit "
                            "because CharSequence is mutable")

        NamedUnit.__init__(self, name, func.inputTypes[:-1], func.returnTypes, True)
        self.token = token
        self.func = func

    def declare(self, code, inputVars, streamVar):
        assert len(inputVars) == len(self.inputTypes)

        code.beginBlock(NamedUnit.signature(self, inputVars, streamVar))
        code.addLine("CharSequence " +
                     tokenSequenceVarName + " = " +
                     self.token.name + ".parseToken(" + streamVar+ ");")

        code.beginBlock("if(" + tokenSequenceVarName + " != null)")

        returnVars = self.func.createCall(code, inputVars + [tokenSequenceVarName], streamVar)

        if returnVars:
            assert len(returnVars) == 1
            # funcs only have one returnType.
            # and they are not ParserUnits
            code.addLine("return " + returnVars[0] + ";")
            code.endBlock() # success parse
            code.addLine("return null;") # alternative fail
        else:
            code.addLine("return true;")
            code.endBlock() # success parse
            code.addLine("return false;") # alternative fail

        code.endBlock()
        return self

################################################################################
## Functions ###################################################################
################################################################################

class Pass(Unit):
    def __init__(self, types):
        Unit.__init__(self, types, types, False)

    def createCall(self, code, inputVars, streamVar):
        return inputVars

    def __str__(self):
        return ""

class FuncUnit(NamedUnit):
    def __init__(self, name, inputTypes, returnTypes):
        NamedUnit.__init__(self, name, inputTypes, returnTypes, False)

    def setBody(self, body):
        self.body = body
        return self

    def declare(self, code, inputVars):
        assert len(inputVars) == len(self.inputTypes)

        code.beginBlock(NamedUnit.signature(self, inputVars, None))
        for line in self.body.split("\n"):
            code.addLine(line)
        code.endBlock()
        return self

################################################################################
## Parsers #####################################################################
################################################################################

class Parser(NamedUnit):
    def __init__(self, name, inputTypes, returnTypes):
        # Although this is reserved for parsers, the definition
        # is not necessarily a parser. Therefore the isParserUnit-flag
        # is set in accordance with definition.
        NamedUnit.__init__(self, name, inputTypes, returnTypes, True)
        self.definition = None

    def setDefinition(self, definition):
        if self.inputTypes != definition.inputTypes:
            raise TypeError("input types do not match")

        if self.returnTypes != definition.returnTypes:
            raise TypeError("return types do not match")

        self.definition = definition
        return self

    def declare(self, code, inputVars, streamVar):
        assert len(inputVars) == len(self.inputTypes)

        # Create constant
        code.beginBlock(NamedUnit.signature(self, inputVars, streamVar))

        # declare status variable
        code.addLine("boolean " + statusVarName + " = true;")

        returnVars = self.definition.createCall(code, inputVars, streamVar)

        if returnVars:
            code.addLine("return " + returnVars[0] + ";")
        elif self.isParserUnit:
            code.addLine("return " + statusVarName + ";")

        code.endBlock()
        return self

################################################################################
## Combinators #################################################################
################################################################################


class Or(Unit):
    def __init__(self, first, second):
        if first.inputTypes != second.inputTypes or first.returnTypes != second.returnTypes:
            raise TypeError("types in 'or' must match")
        if not first.isParserUnit:
            raise TypeError("first element in 'or' must be a parser unit")

        Unit.__init__(self, first.inputTypes, first.returnTypes, second.isParserUnit)

        self.first = first
        self.second = second

    def assignReturnVars(self, code, inputVars, streamVar, returnVars):
        code.addLine("/* " + str(self) + " */")
        self.first.assignReturnVars(code, inputVars, streamVar, returnVars)

        code.beginBlock("if(!" + statusVarName + ")")
        self.second.assignReturnVars(code, inputVars, streamVar, returnVars)

        if not self.second.isParserUnit:
            code.addLine(statusVarName + " = true;")

        code.endBlock()
        code.addLine("/* end " + str(self) + " */")

    def __str__(self):
        return str(self.first) + " | " + str(self.second)

class Then(Unit):
    def __init__(self, left, right):
        overlapLen = min(len(left.returnTypes), len(right.inputTypes))

        overlap = left.returnTypes[-overlapLen:] if overlapLen != 0 else []

        if overlapLen != 0 and right.inputTypes[-overlapLen:] != overlap:
            raise TypeError("overlap in then does not match")

        Unit.__init__(self, left.inputTypes + right.inputTypes[:len(right.inputTypes) - overlapLen],
                      left.returnTypes[:len(left.returnTypes) - overlapLen] + right.returnTypes,
                      left.isParserUnit or right.isParserUnit)

        self.left = left
        self.right = right

    def assignReturnVars(self, code, inputVars, streamVar, returnVars):
        code.addLine("/* " + str(self) + " */")
        nextInputVars = self.left.createCall(code, inputVars, streamVar)

        if self.left.isParserUnit:
            code.beginBlock("if(" + statusVarName + ")")

        localReturnVars = self.right.createCall(code, nextInputVars, streamVar)

        if self.right.isParserUnit:
            code.beginBlock("if(!" + statusVarName + ")")
            code.addLine("parsingError(" + streamVar + ", \"" + str(self.right) + "\");")

        if returnVars:
            if self.right.isParserUnit:
                code.elseBlock()

            # all successful, assign return variables
            # this is empty if there are no return values.
            for lv, rv in zip(returnVars, localReturnVars):
                if lv != rv:
                    code.addLine(lv + " = " + rv + ";")

        if self.right.isParserUnit:
            code.endBlock()

        if self.left.isParserUnit:
            code.endBlock()

        code.addLine("/* end " + str(self) + " */")

    def __str__(self):
        leftString = str(self.left)

        if isinstance(self.left, Or):
            leftString = "(" + leftString + ")"

        rightString = str(self.right)

        if isinstance(self.right, Or):
            rightString = "(" + rightString + ")"

        return leftString + " " + rightString


class Closure(Unit):
    def __init__(self, child):
        if not child.isParserUnit:
            raise TypeError("child of rep must have an optional return value")
        if child.returnTypes != child.inputTypes:
            raise TypeError("in and out type must match in rep")

        Unit.__init__(self, child.inputTypes, child.returnTypes, True)
        self.child = child

class Rep(Closure):
    def __init__(self, child):
        Closure.__init__(self, child)

    def assignReturnVars(self, code, inputVars, streamVar, returnVars):
        assert len(inputVars) == len(returnVars)

        code.addLine("/* " + str(self) + " */")
        for lv, rv in zip(returnVars, inputVars):
            code.addLine(lv + " = " + rv + ";")

        code.beginBlock("for(;;)")
        localReturnVars = self.child.createCall(code, returnVars, streamVar)
        code.beginBlock("if(!" + statusVarName + ")")
        code.addLine(statusVarName + " = true;")
        code.addLine("break;")

        if localReturnVars:
            code.elseBlock()
            for lv, rv in zip(returnVars, localReturnVars):
                code.addLine(lv + " = " + rv + ";")

        code.endBlock()
        code.endBlock()

        code.addLine("/* end " + str(self) + " */")

    def __str__(self):
        childString = str(self.child)

        if isinstance(self.child, Or) or isinstance(self.child, Then):
            childString = "(" + childString + ")"

        return childString + "*"


class Opt(Closure):
    def __init__(self, child):
        Closure.__init__(self, child)

    def assignReturnVars(self, code, inputVars, streamVar, returnVars):
        code.addLine("/* " + str(self) + " */")
        for lv, rv in zip(returnVars, inputVars):
            code.addLine(lv + " = " + rv + ";")

        localReturnVars = self.child.createCall(self, code, inputVars, streamVar)

        if returnVars:
            code.beginBlock("if(" + statusVarName + ")")
            for lv, rv in zip(returnVars, localReturnVars):
                code.addLine(lv + " = " + rv + ";")
            code.endBlock()

        code.addLine(statusVarName + " = true;")

        code.addLine("/* end " + str(self) + " */")

    def __str__(self):
        childString = str(self.child)

        if isinstance(self.child, Or) or isinstance(self.child, Then):
            childString = "(" + childString + ")"

        return childString + "?"
