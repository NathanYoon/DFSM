# Using Pyython we created a lexer using a determenistic finite state algorthm
# where the program takes a file, then proceeds by splitting the file into chars
# Ones split, it goes through various phases. Starting phase being _lexerStart_.
# Once it begins it goes through each function call it contains and runs through 
# its positions. If it encounters an item within the function it calls True and 
# returns to the main staring function to repeat the process until it reaches the
# end of the file.

from queue import Queue
from threading import Thread, current_thread
from string import ascii_letters, digits

# simply keeps track of the already consumed characters in the file
class Consumed(Exception):
    pass

# this displays any halts the program in the case of a mistake in the test files
class LexException(Exception):
    pass


class Lexer(Thread):
    
    operators = "!&%+-*/\|^=~:><."
    seperators = "();{}[],"
    comment = "#"
    
    def __init__(self, inp, que, name="Rat21F lexer"):
        
        super(Lexer, self).__init__()
        self._inProgress_ = inp
        self._que_ = que
        self.name = name
        self._start_ = 0
        self._position_ = 0
        self.line = 1
        self.indentlevels = [0]
        
##############################################################################        
    #"Starting State" / state table
    def _lexerStart_(self):

        while True:
            current = self._currentChar_()

            if current in self.comment:
                return self._comments_

            elif current in ascii_letters:
                return self._lexID_
                
            elif current in digits:
                return self._lexInt_

            elif current in self.seperators:
                return self._lexSeperators_
             
            elif current in self.operators:
                return self._lexOperator_  
            
            elif current == '"' or current == "'":
                self._position_ += 1
                return self._lexString_

            elif current in " \t\n": # ignore whitespace
                self._position_ += 1
                self._start_ = self._position_
                if current == "\n":
                    self.line+=1
                    
            else:
                self._emit("STRING" % self.line)
     
                
    def _comments_(self):
        current = self._currentChar_()
        while current != '\n':
            try:
                current = self._currentChar_()
            except Consumed:
                raise               
            self._position_ += 1     
        self._position_-= 1   
        self._emit("COMMENT")
        return self._lexerStart_
     
        
##############################################################################
    #KEEPS TRACK OF CURRENT STATE
    def _currentChar_(self):
        try:
            return self._inProgress_[self._position_]
        except IndexError:
            raise Consumed("Input stream is consumed")
     
    # PRINTS OR EMITS THE TOKEN TYPE
    def _emit(self, token_type):
        self._que_.put((token_type, self.line, self._inProgress_[self._start_:self._position_]))
        self._start_ = self._position_

##############################################################################
    #OPERATORS WORK
    def _lexOperator_(self):

        prev = self._currentChar_()
        self._position_+=1
        current = self._currentChar_()
        two_chars = prev + current
        if two_chars in ["++","--",">>","<<","==",">","<","!=", "!", "&","&&","^","%"]:
            self._position_ += 1
            self._emit("OPERATOR")
           
        else:
            self._emit("OPERATOR")
        return self._lexerStart_

##############################################################################    
    #SEPERATORS WORK
    def _lexSeperators_(self):
        prev = self._currentChar_()
        self._position_+=1
        current = self._currentChar_()
        two_chars = prev + current
        if two_chars in ["(", ")", "{", "}", "[", "]"]:
            self._position_ += 1
            self._emit("SEPERATOR")
        else:
            self._emit("SEPERATOR")
            return self._lexerStart_
 
##############################################################################
    # STRING IDENTIFIER WORKS CAN BE REMOVED SIMPLY BY REMOVING IN _lexerStart_
    # OR COMMENTING OUT self._emit("STRING")
    def _lexString_(self):
        escape = False
        while True:
            try:
                current = self._currentChar_()
            except Consumed:
                raise LexException("WHOOPS! We had a string here what happened?")
            self._position_ += 1
            if escape:
                escape = False
                continue
            if current == '\\':
                escape = True
            elif current == '"' or current == "'":
                    self._emit("STRING")
                    return self._lexerStart_()
            elif current == "\n":
                self.line += 1
                
##############################################################################         
    # IDENTIFIERS WORK
    def _lexID_(self):
        while True:
            try:
                current = self._currentChar_()
    
            except Consumed:
                self._emit("IDENTIFIER")
                raise
                 
            if current in ascii_letters:
                self._position_ += 1
            elif current in digits:
                self._position_ += 1
            elif current == '_':
                self._position_ += 1
                
            else:
                self._emit("IDENTIFIER")
                return self._lexerStart_

##############################################################################
    # INTEGERS WORK
    def _lexInt_(self):
        while True:
            try:
                current = self._currentChar_()
            except Consumed:
                self._emit("INTEGER")
                raise
                
            if current in digits:
                self._position_ += 1
                
            elif current == ".":
                self._position_ +=1
                return self._lexFloat_
            
            else:
                self._emit("INTEGER")
                return self._lexerStart_
        
##############################################################################        
    # REAL NUMBERS WORKS BASED OF OFF _lexInt_ FUNCTION
    # if a digit is found with a "." then it calls this function to identify it
    def _lexFloat_(self):
        while True:
            try:
                current = self._currentChar_()
            except Consumed:
                self._emit("REAL")
                raise
                
            if current in digits:
                self._position_ += 1
                
            else:
                self._emit("REAL")
                return self._lexerStart_

##############################################################################
    # SIMPLY CLEANS UP THE FILE BY IDENTIFYING ALL DEDENTS IN THE FILE
    # IF UNCOMMENTED IT PRINTS OUT ALL DEDENTS IN THE LEXER
    def _cleanup_(self):
        current_indentation = self.indentlevels.pop()
        while current_indentation != 0:
            self._emit("DEDENT")
            current_indentation = self.indentlevels.pop()
            break
        # ADDS AND "END" TO THE LEXAR TO MARK IT AS FINISHED
        self._emit("END")
        

    # USED TO EXECUTE THE FILE FOR TESTING
    def run(self):
        state = self._lexerStart_
        while True:
            try:
                state = state()
            except Consumed:
                self._cleanup_()
                break
            # Used for testing purposes it displays an error message
            #except LexException as e:
                #print (e.message) 
                #self._emit("END")
                #break


##############################################################################
#testing
##############################################################################

if __name__ == "__main__":
    tokenq = Queue()
    
    #NEED TO FIX COMMENTS AS OF NOW IT DELETES THE WHOLE LINE W/COMMENT
    with open("test.txt") as test:
        myinput = test.read()
        #strip = myinput.strip('#')
    f = open("output.txt", "a")
    # keywords can be added or deleted here whenever needed
    keywords = ["import", "integer", "if", "else", "endif", "while", "for", "print", "cmath", "or", "in",
               "True", "False", "with", "except", "break", "def", "else", "try", "return", "get", "put",
               "raise", "class", "super", "from","self"]

    mylexer = Lexer(myinput, tokenq)
    mylexer.start()

    print("Token --------------------- Lexeme", file = f)
    print("==================================", file = f)
    print("==================================", file = f)
    
    while True:
        tokentype, line, value = tokenq.get()
        token_output = (tokentype)
        # GOES THROUGH TOKENS AND WHATEVER TOKENS MATCH WHAT IS IN THE keywords 
        # LIST THEN IT PRINTS IT AS A KEYWORD

        if value in keywords:
            print("|", "KEYWORD", "---------------------", value, file = f)
        else:
            print("|", token_output, "---------------------", value, file = f)       
        # ONCE THE THE LOOP REACHES THE TOKENTYPE END IT BREAKS AND END THE PROGRAM
        if token_output == "END":
            break