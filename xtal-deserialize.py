import sys, struct
from collections import namedtuple

class SerOp:
    pass
for i, name in enumerate('''
SERIAL_NEW
NAME
REFERENCE
TNULL
TUNDEFINED
TFALSE
TTRUE
TINT32
TINT64
TFLOAT32
TFLOAT64
TSTRING8
TSTRING16
TSTRING32
TID8
TID16
TID32
TARRAY
TMAP
TVALUES
'''.strip().split()):
    setattr(SerOp, name, i)

class XNull: pass
class XUndefined: pass
class XId(str): pass

XScopeInfo = namedtuple('XScopeInfo', 'pc kind flags variable_identifier_offset variable_offset variable_Size')
XClassInfo = namedtuple('XClassInfo', 'scope_info instance_variable_size instance_variable_identifier_offset name_number mixins')
XFunInfo = namedtuple('XFunInfo', 'scope_info max_stack max_variable name_number min_param_count max_param_count')
XExceptInfo = namedtuple('XExceptInfo', 'catch_pc finally_pc end_pc')
XLineNumberInfo = namedtuple('XLineNumberInfo', 'start_pc lineno')

class Inst:
    classes = {}

def inst(name, op, fields):
    fields = fields.split()
    cls = namedtuple(name, fields[1::2])
    cls.FMT = '<B'
    for fmt in ''.join(fields[::2]):
        cls.FMT += 'x' * (-struct.calcsize(cls.FMT) % struct.calcsize(fmt))
        cls.FMT += fmt
    cls.OP = op
    cls.SIZE = struct.calcsize(cls.FMT)
    setattr(Inst, name, cls)
    Inst.classes[op] = cls

def inst_rts(name, op, **kwargs):
    inst(name, op, 'b result b target b stack_base', **kwargs)
def inst_rlrsa(name, op, **kwargs):
    inst(name, op, 'b result b lhs b rhs b stack_base B assign', **kwargs)
def inst_lrs(name, op, **kwargs):
    inst(name, op, 'b lhs b rhs b stack_base', **kwargs)

inst('Line', 0, '')
inst('LoadValue', 1, 'b result B value')
inst('LoadConstant', 2, 'b result H value_number')
inst('LoadInt1Byte', 3, 'b result b value')
inst('LoadFloat1Byte', 4, 'b result b value')
inst('LoadCallee', 5, 'b result')
inst('LoadThis', 6, 'b result')
inst('Copy', 7, 'b result b target')
inst_rts('Inc', 8)
inst_rts('Dec', 9)
inst_rts('Pos', 10)
inst_rts('Neg', 11)
inst_rts('Com', 12)
inst_rlrsa('Add', 13)
inst_rlrsa('Sub', 14)
inst_rlrsa('Cat', 15)
inst_rlrsa('Mul', 16)
inst_rlrsa('Div', 17)
inst_rlrsa('Mod', 18)
inst_rlrsa('And', 19)
inst_rlrsa('Or',  20)
inst_rlrsa('Xor', 21)
inst_rlrsa('Shl', 22)
inst_rlrsa('Shr', 23)
inst_rlrsa('Ushr', 24)
inst('At', 25, 'b result b target b index b stack_base')
inst('SetAt', 26, 'b result b target b index b stack_base')
inst('Goto', 27, 'h address')
inst('Not', 28, 'b result b target')
inst('If', 29, 'b target h address_true h address_false')
inst_lrs('IfEq', 30)
inst_lrs('IfLt', 31)
inst_lrs('IfRawEq', 32)
inst_lrs('IfIs', 33)
inst_lrs('IfIn', 34)
inst('IfUndefined', 35, 'b target h address_true h address_false')
inst('IfDebug', 36, 'h address')
inst('Push', 37, 'b target')
inst('Pop', 38, 'b result')
inst('AdjustValues', 39, 'B stack_base B result_count B need_result_count')
inst('LocalVariable', 40, 'b result H number B depth')
inst('SetLocalVariable', 41, 'b target H number B depth')
inst('InstanceVariable', 42, 'b result h info_number B number')
inst('SetInstanceVariable', 43, 'b value h info_number B number')
inst('InstanceVariableByName', 44, 'b result H identifier_number')
inst('SetInstanceVariableByName', 45, 'b value H identifier_number')
inst('FilelocalVariable', 46, 'b result H value_number')
inst('SetFilelocalVariable', 47, 'b value H value_number')
inst('FilelocalVariableByName', 48, 'b result H identifier_number')
inst('SetFilelocalVariableByName', 49, 'b value H identifier_number')

class NoSlots(object):
    pass
class XCode(NoSlots, namedtuple('XCode', 'codes scope_info class_info except_info line_number_info once_count source_file_name identifier_table value_table breakpoint_cond_map')):
    def __init__(self, *args, **kwargs):
        super(XCode, self).__init__(*args, **kwargs)
        self.decode = []
        codes = bytearray(struct.pack('<%sH' % len(self.codes), *self.codes))
        i = 0
        while i < len(codes):
            oi = i
            op = codes[i]
            cls = Inst.classes[op]
            print cls, cls.FMT
            inst = cls(*struct.unpack(cls.FMT, codes[i:i+cls.SIZE])[1:])
            i += cls.SIZE
            self.decode.append(inst)


class Deserializer:
    def __init__(self, data):
        self.data = bytearray(data)
        self.i = 0
        self.values = []
    def read(self, n):
        assert self.i + n <= len(self.data)
        ret = self.data[self.i:self.i+n]
        self.i += n
        return ret
    def readx(self, fmt):
        fmt = '>' + fmt
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))[0]
    def read8(self):
        return self.read(1)[0]
    def deserialize(self):
        op = self.read8()
        if op == SerOp.SERIAL_NEW:
            class_ptr = self.deserialize()
            the_map = self.deserialize()
            self.values.append('<unknown deserialize result>')
            return ('serial_new', class_ptr, the_map)
        elif op == SerOp.NAME:
            vi = len(self.values)
            self.values.append(None)
            v = self.values[vi] = self.demangle(self.deserialize())
            return v
        elif op == SerOp.REFERENCE:
            return self.values[self.readx('I')]
        elif op == SerOp.TNULL:
            return XNull()
        elif op == SerOp.TUNDEFINED:
            return XUndefined()
        elif op == SerOp.TINT32:
            return self.readx('i')
        elif op == SerOp.TFLOAT32:
            return self.readx('f')
        elif op == SerOp.TINT64:
            return self.readx('q')
        elif op == SerOp.TFLOAT64:
            return self.readx('d')
        elif op == SerOp.TSTRING8:
            return self.deserialize_string('B', False)
        elif op == SerOp.TID8:
            return self.deserialize_string('B', True)
        elif op == SerOp.TSTRING16:
            return self.deserialize_string('H', False)
        elif op == SerOp.TID16:
            return self.deserialize_string('H', True)
        elif op == SerOp.TSTRING32:
            return self.deserialize_string('I', False)
        elif op == SerOp.TID32:
            return self.deserialize_string('I', True)
        elif op == SerOp.TARRAY:
            count = self.readx('I')
            ret = [self.deserialize() for i in xrange(count)]
            self.values.append(ret)
            return ret
        elif op == SerOp.TVALUES:
            head = self.deserialize()
            tail = self.deserialize()
            ret = (head, tail)
            self.values.append(ret)
            return ret
        elif op == SerOp.TMAP:
            count = self.readx('I')
            ret = {self.deserialize(): self.deserialize() for i in xrange(count)}
            self.values.append(ret)
            return ret
        elif op == SerOp.TTRUE:
            return True
        elif op == SerOp.TFALSE:
            return False
        elif op == ord('x'):
            return self.deserialize_code()

    def deserialize_string(self, charfmt, intern):
        size = self.readx('I')
        string = u''
        for i in xrange(size):
            string += unichr(self.readx(charfmt))
        if intern:
            string = XId(string)
        self.values.append(string)
        return string

    def deserialize_code(self):
        vi = len(self.values)
        self.values.append(None)
        assert str(self.read(3)) == 'tal'
        version = self.read(2)
        other = self.read(2)
        assert version[0] == 2 and version[1] == 0
        codes = [self.readx('H') for i in xrange(self.readx('I'))]
        scope_info = [self.deserialize_scope_info() for i in xrange(self.readx('H'))]
        class_info = [self.deserialize_class_info() for i in xrange(self.readx('H'))]
        fun_info = [self.deserialize_fun_info() for i in xrange(self.readx('H'))]
        except_info = [self.deserialize_except_info() for i in xrange(self.readx('H'))]
        line_number_info = [self.deserialize_line_number_info() for i in xrange(self.readx('H'))]
        once_count = self.readx('H')
        source_file_name = self.deserialize()
        identifier_table = [self.deserialize() for i in xrange(self.readx('H'))]
        value_table = [self.deserialize() for i in xrange(self.readx('H'))]
        breakpoint_cond_map = self.deserialize()

        ret = self.values[vi] = XCode(codes, scope_info, class_info, except_info, line_number_info, once_count, source_file_name, identifier_table, value_table, breakpoint_cond_map)
        return ret

    def deserialize_scope_info(self):
        return XScopeInfo(self.readx('I'), self.readx('B'), self.readx('B'), self.readx('H'), self.readx('H'), self.readx('H'))

    def deserialize_class_info(self):
        return XClassInfo(self.deserialize_scope_info(), self.readx('H'), self.readx('H'), self.readx('H'), self.readx('B'))

    def deserialize_fun_info(self):
        return XFunInfo(self.deserialize_scope_info(), self.readx('H'), self.readx('H'), self.readx('H'), self.readx('B'), self.readx('B'))

    def deserialize_except_info(self):
        return XExceptInfo(self.readx('I'), self.readx('I'), self.readx('I'),)

    def deserialize_line_number_info(self):
        return XLineNumberInfo(self.readx('I'), self.readx('H'))

stuff = Deserializer(open(sys.argv[1]).read()).deserialize()
if isinstance(stuff, XCode):
    stuff.disassemble()
else:
    print stuff
