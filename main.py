import argparse
import string
import random
from typing import List
from collections.abc import Iterable
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

class Word:
    def __init__(self, value: str):
        self.value = value

    def compile(self) -> list:
        return ["\t", "jsr ", self.value, '\n']

    def __repr__(self):
        return ''.join(self.compile())

class Num:
    def __init__(self, value: int):
        self.value = value
    
    def compile(self) -> list:
        return ["\t", "push ", '#' + str(self.value), '\n']

    def __repr__(self):
        return ''.join(self.compile())

class If:
    def __init__(self, body: list, else_: list):
        self.body = body
        self.else_ = else_
        self.mangle = ''.join([random.choice(string.ascii_letters), random.choice(string.ascii_letters), random.choice(string.ascii_letters)])
    
    def compile(self) -> list:
        if self.else_ != None:
            return ['\t', 'PLA ', '\n',
                    '\t', 'CMP ', '#0', '\n',
                    '\t', 'BNE ', self.mangle + 'if', '\n',
                    '\t', 'BEQ ', self.mangle + 'else', '\n',
                    '\t', 'JMP ', self.mangle + 'then', '\n',
                    self.mangle + 'if:' + '\n',
                    self.body.compile(),
                    self.mangle + 'else:' + '\n',
                    self.else_.compile(),
                    self.mangle + 'then:' + '\n']
        else:
            return ['\t', 'PLA ', '\n',
                    '\t', 'CMP ', '#0', '\n',
                    '\t', 'BNE ', self.mangle + 'if', '\n',
                    '\t', 'JMP ', self.mangle + 'then', '\n',
                    self.mangle + 'if:' + '\n',
                    self.body.compile(),
                    self.mangle + 'then:' + '\n']
    
    def __repr__(self):
        return ''.join(flatten(self.compile()))

class Inline:
    def __init__(self, asm: str):
        self.asm = asm
    
    def compile(self) -> list:
        return ["\t", self.asm, '\n']
    
    def __repr__(self):
        return ''.join(self.compile())

class Block:
    def __init__(self, body: list):
        self.body = body
    
    def compile(self) -> list:
        return [i.compile() for i in self.body]
    
    def __repr__(self):
        return ''.join(flatten(self.compile()))

class WordDef:
    def __init__(self, name: str, body: Block):
        self.name = name
        self.body = body
    
    def compile(self) -> list:
        return [self.name + ':', '\n',
               self.body.compile(), 
               '\t', 'RTS', '\n']
    
    def __repr__(self):
        return ''.join(flatten(self.compile()))

def lex(program: str):
    lexemes = program.split(' ')
    tokens = []
    for i in lexemes:
        if i == ':':
            tokens.append((':', 'COL'))
        elif i == ';':
            tokens.append((';', 'SEMIC'))
        elif i == '{':
            tokens.append(('{', 'LBRAC'))
        elif i in ('if', 'IF'):
            tokens.append(('if', 'IF'))
        elif i in ('else', 'ELSE'):
            tokens.append(('else', 'ELSE'))
        elif i in ('then', 'THEN'):
            tokens.append(('then', 'THEN'))
        elif i == '}':
            tokens.append(('}', 'RBRAC'))
        else:
            try: tokens.append((int(i), 'INT'))
            except ValueError:
                tokens.append((i, 'WORD'))
    return tokens

class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens

    def Eat(self, type: str):
        t = self.tokens.pop(0)
        assert t[1] == type, '? EXPECTED ' + type
        return t[0]

    def Peek(self, type):
        return len(self.tokens) > 0 and self.tokens[0][1] == type

    def IfStmt(self) -> If:
        self.Eat('IF')
        body = self.Block()
        if self.Peek('THEN'):
            self.Eat('THEN')
            return If(body, None)
        elif self.Peek('ELSE'):
            self.Eat('ELSE')
            else_ = self.Block()
            self.Eat('THEN')
            return If(body, else_)
        else:
            assert False, '? EXPECTED THEN OR ELSE'

    def Word(self) -> Word:
        return Word(self.Eat('WORD'))

    def Int(self) -> Num:
        return Num(self.Eat('INT'))

    def Inline(self) -> Inline:
        self.Eat('LBRAC')
        b = []
        while not self.Peek('RBRAC'):
            b.append(self.tokens.pop(0)[0])
        self.Eat('RBRAC')
        return Inline(' '.join(b))

    def Block(self) -> Block:
        b = []
        while self.Peek('IF') or self.Peek('WORD') or self.Peek('INT') or self.Peek('LBRAC'):
            if self.Peek('IF'):
                b.append(self.IfStmt())
            elif self.Peek('WORD'):
                b.append(self.Word())
            elif self.Peek('INT'):
                b.append(self.Int())
            elif self.Peek('LBRAC'):
                b.append(self.Inline())
            else:
                assert False, '? EXPECTED IF, WORD, INT, OR INLINE'
        return Block(b)

    def WordDef(self) -> WordDef:
        self.Eat('COL')
        name = self.Eat('WORD')
        body = self.Block()
        self.Eat('SEMIC')
        return WordDef(name, body)
    
    def Parse(self) -> list:
        b = []
        while self.Peek('IF') or self.Peek('WORD') or self.Peek('INT') or self.Peek('LBRAC') or self.Peek('COL'):
            if self.Peek('IF'):
                b.append(self.IfStmt())
            elif self.Peek('WORD'):
                b.append(self.Word())
            elif self.Peek('INT'):
                b.append(self.Int())
            elif self.Peek('LBRAC'):
                b.append(self.Inline())
            elif self.Peek('COL'):
                b.append(self.WordDef())
            else:
                assert False, '? EXPECTED IF, WORD, INT, OR INLINE'
        return b

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="the file to compile", type=str)
    args = parser.parse_args()
    with open(args.file) as f:
        program = f.read()
    compiled = Parser(lex(program)).Parse()
    code = []
    sub = []
    for i in compiled:
        if isinstance(i, WordDef):
            sub.append(flatten(i.compile()))
        else:
            code.append(flatten(i.compile()))
    code = [i for i in flatten(code)]
    sub = [i for i in flatten(sub)]
    print(open('kernel.s').read().replace(';cd', ''.join(code)).replace(';sr', ''.join(sub)))

if __name__ == "__main__":
    main()

