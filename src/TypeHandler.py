# encoding=utf8
from TypeChecker import *


class ColumnParseError(Exception):
    def __init__(self, col, msg):
        self.col = col
        Exception.__init__(self, msg)


CellData = namedtuple('CellData', 'value info')


class TypeHandler:
    inst = None  # type: TypeHandler
    typeAttrsNames = 'object pk key unique getter type defVal array fields map range arrayRange'.split()

    def __init__(self):
        TypeHandler.inst = self
        self.line = 0

        types = [
            {
                'token': '',
                'doc': 'empty type, internal use. handle all typeless values',
                'simpleType': True,
                'parser': lambda x, i: x,
            },
            {
                'token': 'int',
                'simpleType': True,
                'default': '0',
                'isNumber': True,
                'parser': lambda x, i: int(x)
            },
            {
                'token': 'auto',
                'simpleType': True,
                'doc': 'reuse type of other column(can cross table), e.g. col: auto typeof(<otherTable.>col)',
            },
            {
                'token': 'uint',
                'doc': 'unsigned int',
                'simpleType': True,
                'default': '0',
                'isNumber': True,
                'parser': lambda x, i: int(x) if int(x) >= 0 else assertExpr(False, 'uint type must be positive: %s' % x)
            },
            {
                'token': 'bool',
                'doc': 'true: 1 or true; false: 0 or false',
                'simpleType': True,
                'default': 'false',
                'parser': self.parseBool
            },
            {
                'token': 'float',
                'simpleType': True,
                'default': '0.0',
                'isNumber': True,
                'parser': lambda x, i: float(x)
            },
            {
                'token': 'str',
                'default': '',
                'simpleType': True,
                'parser': lambda x, i: x if isinstance(x, unicode) else str(x)
            },
            {
                'token': 'object',
                'doc': 'parse to user defined structure, usage: {f1:type ~ f2:type} [rangeCheckers]',
                'simpleType': False,
                'parser': self.parseUser
            },
        ]
        if 'customTypes' in appCfg:
            types.extend(appCfg['customTypes'])

        qualifiers = [
            {'token': 'pk', 'doc': 'has [unique, getter] attribute, primary unique id of one row, one table should has only one pk column'},
            {'token': 'key', 'doc': 'has [unique, getter] attribute, generate as a map with this filed as key'},
            {'token': 'unique', 'doc': 'has [notNull] attribute, unique in this table'},
            {'token': 'notNull', 'doc': 'should not be empty'},
            {'token': 'getter', 'doc': 'generate checked getter function'},
            {'token': 'fmt', 'doc': 'can use fmt expression'},
            {'token': 'comment', 'doc': 'wont generate anything'},
            {'token': 'map(table.col)', 'doc': 'map to another table\'s column'},
            {'token': 'typeof(table.col)', 'doc': 'use with auto to map to another table\'s column'},
        ]

        if 'typeAlias' in appCfg:
            self.typeAlias = OrderedDict((i['token'], i) for i in appCfg['typeAlias'])
            self.aliasParsed = {}

        self.types = OrderedDict((i['token'], i) for i in types)
        self.qualifiers = OrderedDict((i['token'], i) for i in qualifiers)

    @cached
    def getSimpleTypes(self):
        return [k for k, v in self.types.iteritems() if v['simpleType']]

    @cached
    def getCompositeTypes(self):
        return [k for k, v in self.types.iteritems() if not v['simpleType']]

    @cached
    def getNumberTypes(self):
        return [k for k, v in self.types.iteritems() if v.get('isNumber', False)]

    @classmethod
    def copyTypeAttrs(cls, s, d):
        for k in cls.typeAttrsNames:
            v = getattr(s, k)
            if v:
                setattr(d, k, getattr(s, k))

    @classmethod
    def mergeTypeAttrs(cls, s, d):
        for k in cls.typeAttrsNames:
            v = getattr(s, k)
            if v:
                setattr(d, k, v)

    def onTypeParsed(self, info):
        if info.name.startswith('comment'):
            info.comment = 'comment'

        if info.object <> '':
            info.type = 'object'

        if info.pk == 'pk' or info.key == 'key':
            info.unique = 'unique'
            info.getter = 'getter'

        if info.unique <> '':
            info.notNull = 'notNull'

        if info.type not in self.types and info.type not in self.typeAlias:
            raise ColumnParseError(info.name, 'unknown type:%s' % info.type)

        if info.typeof <> '':
            if info.type <> 'auto':
                raise ColumnParseError(info.name, 'usage: col: auto typeof(targetColumn)')

            tarTb, tarCol = info.table, info.typeof.target
            if '.' in tarCol:
                tarTb, tarCol = info.typeof.target.split('.')
                tarTb = info.table.app.getTable(tarTb)
            tar = [i for i in tarTb.fieldsList if i.name == tarCol]
            if not tar:
                raise ColumnParseError(info.name, 'target column of typeof not exists: %s' % info.typeof.target)

            self.copyTypeAttrs(tar[0], info)

        if info.defVal == '':
            if info.type in self.types:
                t = self.types[info.type]
                if 'default' in t:
                    if info.array == '':
                        info.defVal = t['default']
                    else:
                        info.defVal = ''

        if info.fields <> '':
            for i in info.fields:
                self.onTypeParsed(i)

        if info.map <> '':
            info.map = info.map.target.split('.')

    @cached
    def processAlias(self, info, parser, tb):
        if not self.aliasParsed:
            self.aliasParsed = {token: parser.parseColumn(token + ':' + a['type'], tb) for token, a in self.typeAlias.iteritems()}

        if info.type <> '':
            def walk(i):
                if i.type in self.typeAlias:
                    self.copyTypeAttrs(self.aliasParsed[i.type], i)
                if i.fields:
                    for j in info.fields:
                        walk(j)

            walk(info)
        return info

    def parseData(self, v, info, line):
        self.line = line

        if v == '':
            if info.notNull <> '':
                raise ColumnParseError(info.name, 'value of notNull type can not be empty')
            return info.defVal

        t = self.types[info.type]
        if 'parser' in t:
            p = t['parser']
            if info.array <> '':
                elemInfo = info.copy()
                elemInfo.array = ''
                elemInfo.arrayRange = ''
                elemInfo.table = info.table
                v = map(lambda e: (p(e, info), elemInfo), str(v).split(';'))
            else:
                v = p(v, info)

        return CellData(v, info)

    @staticmethod
    def parseBool(v, info):
        if v in (True, 'true', '1', 1):
            return True
        assert v in (False, 'false', '0', 0), 'Invalid bool value: %s' % v
        return False

    def hasDefVal(self, i):
        return i.defVal.value <> '' or i.type == 'str'

    def parseUser(self, s, info):
        r = {}
        l = s.split('~')
        for f, v, in zip(info.fields, l):
            r[str(f.name)] = self.parseData(v, f, self.line)

        size = len(l)
        if 0 < size < len(info.fields):
            for i in info.fields[size:]:
                if self.hasDefVal(i):
                    r[i.name] = i.defVal
        assert len(r) == len(info.fields), 'Fields count incorrect: need %d got %s' % (len(info.fields), len(l))
        return r

    def printHelp(self, o):
        o.write("""      
### Syntax
``` 
    colDef => colName : type qualifiers
    type => typeDef [rangeExpression] = defaultValue
    typeDef => simpleType | { colDef ~ colDef ... } | type *    
    simpleType => int | float | str ...
    *: array
```
        """)

        o.write('\n-------- types ---------\n')
        for k, v in self.types.iteritems():
            if k:
                o.write('- %-10s: %s\n' % (k, v['doc'] if 'doc' in v else '<no doc>'))
                if 'default' in v:
                    o.write('\t default: %s\n' % v['default'])
            if k == 'object':
                o.write('\n-------- Custom types --------\n')

        o.write('\n-------- qualifiers --------\n')
        for k, v in self.qualifiers.iteritems():
            o.write('- %-10s: %s\n' % (k, v['doc'] if 'doc' in v else '<no doc>'))

        o.write('\n-------- type alias --------\n')
        for k, v in self.typeAlias.iteritems():
            o.write('- %-10s: %s\n' % (k, v['doc'] if 'doc' in v else '<no doc>'))

        TypeChecker.inst.printCheckers(o)
