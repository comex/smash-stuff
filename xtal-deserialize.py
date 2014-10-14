import sys, struct
from collections import namedtuple

class Op:
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
    setattr(Op, name, i)

class XNull: pass
class XUndefined: pass
class XId(str): pass

XScopeInfo = namedtuple('XScopeInfo', 'pc kind flags variable_identifier_offset variable_offset variable_Size')
XClassInfo = namedtuple('XClassInfo', 'scope_info instance_variable_size instance_variable_identifier_offset name_number mixins')
XFunInfo = namedtuple('XFunInfo', 'scope_info max_stack max_variable name_number min_param_count max_param_count')
XExceptInfo = namedtuple('XExceptInfo', 'catch_pc finally_pc end_pc')
XLineNumberInfo = namedtuple('XLineNumberInfo', 'start_pc lineno')
XClass = namedtuple('XClass', 'codes scope_info class_info except_info line_number_info once_count source_file_name identifier_table value_table breakpoint_cond_map')

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
        if op == Op.SERIAL_NEW:
            class_ptr = self.deserialize()
            the_map = self.deserialize()
            self.values.append('<unknown deserialize result>')
            return ('serial_new', class_ptr, the_map)
        elif op == Op.NAME:
            vi = len(self.values)
            self.values.append(None)
            v = self.values[vi] = self.demangle(self.deserialize())
            return v
        elif op == Op.REFERENCE:
            return self.values[self.readx('I')]
        elif op == Op.TNULL:
            return XNull()
        elif op == Op.TUNDEFINED:
            return XUndefined()
        elif op == Op.TINT32:
            return self.readx('i')
        elif op == Op.TFLOAT32:
            return self.readx('f')
        elif op == Op.TINT64:
            return self.readx('q')
        elif op == Op.TFLOAT64:
            return self.readx('d')
        elif op == Op.TSTRING8:
            return self.deserialize_string('B', False)
        elif op == Op.TID8:
            return self.deserialize_string('B', True)
        elif op == Op.TSTRING16:
            return self.deserialize_string('H', False)
        elif op == Op.TID16:
            return self.deserialize_string('H', True)
        elif op == Op.TSTRING32:
            return self.deserialize_string('I', False)
        elif op == Op.TID32:
            return self.deserialize_string('I', True)
        elif op == Op.TARRAY:
            count = self.readx('I')
            ret = [self.deserialize() for i in xrange(count)]
            self.values.append(ret)
            return ret
        elif op == Op.TVALUES:
            head = self.deserialize()
            tail = self.deserialize()
            ret = (head, tail)
            self.values.append(ret)
            return ret
        elif op == Op.TMAP:
            count = self.readx('I')
            ret = {self.deserialize(): self.deserialize() for i in xrange(count)}
            self.values.append(ret)
            return ret
        elif op == Op.TTRUE:
            return True
        elif op == Op.TFALSE:
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

        ret = self.values[vi] = XClass(codes, scope_info, class_info, except_info, line_number_info, once_count, source_file_name, identifier_table, value_table, breakpoint_cond_map)
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

print Deserializer(open(sys.argv[1]).read()).deserialize()
