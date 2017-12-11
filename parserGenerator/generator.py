def failCheck(type, var):
    if type == None:
        return "!" + var
    else:
        return var + " == null"

def successCheck(type, var):
    if type == None:
        return var
    else:
        return var + " != null"

class CodeGenerator:
    def __init__(self):
        self.varCount = 0
        self.indent = 0
        self.blockJustEnded = False
        self.blockJustStarted = True

    def addLine(self, line, isBlockStart = False, isBlockEnd = False):
        if isBlockStart and not self.blockJustStarted:
            print("")
        elif self.blockJustEnded and not isBlockEnd:
            print("")
        
        print("    " * self.indent + line)
        self.blockJustEnded = False
        self.blockJustStarted = False
    
    def beginBlock(self, header):
        self.addLine(header + " {", True, False)
        self.indent += 1
        self.blockJustStarted = True

    def elseBlock(self):
        self.indent -= 1
        self.addLine("} else {", False, True)
        self.indent += 1
        self.blockJustStarted = True
        
    def endBlock(self):
        self.indent -= 1
        
        if self.indent == 1:
            self.varCount = 0
        
        self.addLine("}", False, True)
        self.blockJustEnded = True
        
    def createVar(self, type, name):
        if name == None:
            name = "var" + str(self.varCount)
            self.varCount += 1
    
        if type == None:
            type = "boolean"
            init = "false"
        else:
            init = "null"
    
        self.addLine(type + " " + name + " = " + init + ";")
        return name
