# encoding=utf8
from Utils import *

'''
TODO: 
- 支持？表达式
'''


class TypeChecker:
    inst = None  # type: TypeChecker

    def __init__(self, app, typeHandler):
        """

        :type app: App
        :type typeHandler: TypeHandler
        """
        TypeChecker.inst = self
        self.values = []
        self.app = app
        self.evalDebug = False
        self.line = 0
        self.typeHandler = typeHandler
        self.ops = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.div,
            '==': lambda a, b: a == b,
            '<=': lambda a, b: a <= b,
            '<': lambda a, b: a < b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            '!=': lambda a, b: a != b,
            '&&': operator.and_,
            '||': operator.or_,
        }

    def exceptNumberType(self, info):
        assert info.type in self.typeHandler.getNumberTypes(), 'need a number, got a %s' % info.type

    def clearCache(self):
        self.lastFolder = ''
        self.files = []

    def checkValue(self, v, info, line):
        self.line = line

        if info.array <> '':
            for i, subInfo in v:
                self.checkValue(i, subInfo, line)
            self.checkRange(v, info, info.arrayRange)
            return

        if info.object <> '' and v:
            for subInfo in info.fields:
                self.checkValue(v[subInfo.name].value, subInfo, line)

        self.checkRange(v, info, info.range)

    def checkRange(self, v, info, range):
        if range == '': return

        self.values.append([v, info])
        exprVal = self.eval_(range)
        assert exprVal, 'range check failed: %s' % (str(range).replace('[', '').replace(']', ''))
        self.values.pop()

    def eval_(self, expr):
        if isinstance(expr, (str, unicode)):
            try:
                return int(expr)
            except:
                pass
            try:
                return float(expr)
            except:
                pass
            return expr

        if expr.op != '':
            r = self.ops[expr.op](self.eval_(expr.left), self.eval_(expr.right))
            if self.evalDebug: print expr, '\t=', r
            return r

        elif expr.func != '':
            try:
                func = getattr(TypeChecker, 'check_%s' % expr.func)
                r = func(self, [self.eval_(i) for i in expr.args])
                if self.evalDebug: print expr, '\t=', r
                return r
            except AssertionError, e:
                raise AssertionError, '%s\n in range function: %s' % (e, expr.func), sys.exc_info()[2]

        elif expr.left != '':
            return self.eval_(expr.left)

        assert False, 'invalid type of ast to eval:%s' % expr

    @classmethod
    def printCheckers(cls, o):
        o.write('\n======= range functions =========\n')
        for k, v in sorted(cls.__dict__.iteritems()):
            if k.startswith('check_'):
                o.write('%-10s:\n' % k.split("_")[1])
                o.write(u8encode('\t%s\n' % (v.__doc__ or 'no doc')))
                o.write('\n')

    def check_unique(self, args):
        """multiple columns as a unique key,
        usage: itemID : int [unique(skillID)], unique key using (itemID, skillID).
        """

        v, info = self.values[-1]
        table = info.table
        fields = tuple([info.name] + args)
        row = table.getRow(self.line)
        val = tuple(row[f].value for f in fields)
        assert val not in table.uniqueCol[fields], 'unique checking failed: %s, duplicated value %s' % (fields, val)
        table.uniqueCol[fields].add(val)
        return True

    def check_sum(self, args):
        """usage: sum(fieldName)
        return sum of specify field of the array
        """

        v, info = self.values[-1]
        assert info.array <> '', 'need a array type'

        total = 0
        for i, elemInfo in v:
            if len(args) == 1:
                assert info.type == 'object', 'need a object type, got %s' % info.type
                vv, elemInfo = i[args[0]]
            else:
                vv = i
            assert elemInfo.type in self.typeHandler.getNumberTypes(), 'need a number, got a %s' % elemInfo.type
            total += vv
        return total

    def check_floatEq(self, args):
        return abs(args[0] - args[1]) <= 0.000001

    def check_ref(self, args):
        """usage: ref(table.columnName)
        check if value is in target column of table"""

        v, info = self.values[-1]
        assert re.match('\w*\.\w*', args[0]), 'incorrect argument: %s, should be like <table>.<column>' % args[0]
        refTable, refColumn = args[0].split('.')

        target = self.app.getTable(refTable)
        assert refColumn in target.fields, 'invalid ref: column %s not exists' % refColumn
        assert [row for row in target.data if v == row[refColumn].value], 'invalid ref: %s not found in %s.%s' % (v, refTable, refColumn)
        return True

    def check_refWhenNotNull(self, args):
        """usage: refWhenNotNull(table.columnName)
        like ref but only do check when value is not null."""

        v, info = self.values[-1]
        if v == info.defVal.value:
            return True
        return self.check_ref(args)

    def check_range(self, args):
        """usage: range(0,100)
        check if value is in range[min,max]"""

        v, info = self.values[-1]
        self.exceptNumberType(info)
        minVal, maxVal = args
        assert v >= minVal, 'range error: %s should not below %s' % (v, minVal)
        assert v <= maxVal, 'range error: %s should not larger than %s' % (v, maxVal)
        return True

    def check_min(self, args):
        """usage: min(0)
        check if value is lager than or equal to 0"""

        v, info = self.values[-1]
        self.exceptNumberType(info)
        assert v >= args[0], 'range error: %s should not below %s' % (v, args[0])
        return True

    def check_max(self, args):
        """usage: max(100)
        check if value is less than or equal to 100"""

        v, info = self.values[-1]
        self.exceptNumberType(info)
        assert v <= args[0], 'range error: %s should not larger than %s' % (v, args[0])
        return True

    def check_len(self, args):
        """usage:
        len()>0 or
        len(field)>0 for object type"""
        v, info = self.values[-1]
        assert info.type in 'str loc', 'need a str, got a %s' % info.type
        if len(args) == 1:
            assert info.type == 'object', 'need a object, got a %s' % info.type
            return len(v[args[0]])
        return len(v)

    def check_value(self, args):
        """usage:
        value()>0 or
        value(field)>0 for object type"""
        v, info = self.values[-1]
        if len(args) == 1:
            assert info.type == 'object', 'need a object, got a %s' % info.type
            return v[args[0]]
        return v

    def check_fileExists(self, args):
        """usage:
        fileExists('Assets/Builds/UI/'+value()+'.prefab')
        wont check empty str. """
        v, info = self.values[-1]
        if v == '':
            return True
        assert info.type == 'str', 'need a str, got a %s' % info.type
        p = os.path.join(appCfg['clientRoot'], args[0])
        assert os.path.isfile(p), 'file not exists: %s' % p
        return True

    def check_fileExistsUnder(self, args):
        """usage:
                fileExistsUnder('Assets/Builds/UI/',value()+'.prefab')
                wont check empty str. """
        v, info = self.values[-1]
        if v == '':
            return True
        assert info.type == 'str', 'need a str, got a %s' % info.type
        p = os.path.join(appCfg['clientRoot'], args[0])
        if not hasattr(self, 'lastFolder') or self.lastFolder <> p:
            self.lastFolder = p
            self.files = [os.path.basename(f) for f in walk(p)]
        assert args[1] in self.files, 'file %s not exists under %s' % (args[1], p)
        return True
