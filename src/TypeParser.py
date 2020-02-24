from TypeHandler import *

identifier = pp.Regex(r'[\w\d\.]+')
str_ = pp.QuotedString("'")
num = pp.Word(pp.nums + '-.')
value = num | str_ | identifier


def genQualifiers():
    q = [i[0] for i in TypeHandler.inst.qualifiers.iteritems() if '(' not in i[1]]
    r = pp.Keyword(q[0])(q[0])
    for i in q[1:]:
        r = r | pp.Keyword(i)(i)
    r = r | (pp.Keyword('map') + pp.Suppress('(') + identifier('target') + pp.Suppress(')'))('map')
    r = r | (pp.Keyword('typeof') + pp.Suppress('(') + identifier('target') + pp.Suppress(')'))('typeof')
    return r


class TypeParser:
    inst = None  # type: TypeParser

    def __init__(self):
        TypeParser.inst = self

        expr = pp.Forward()
        args = expr + pp.ZeroOrMore(pp.Suppress(',') + expr)
        func = pp.Group(identifier('func') + pp.Suppress('(') + pp.Optional(args)('args') + pp.Suppress(')'))
        factor = func | value | pp.Group(pp.Suppress('(') + expr + pp.Suppress(')'))
        mulOne = pp.Group(factor('left') + pp.Optional(pp.oneOf('* /')('op') + factor('right')))
        mul = pp.Group(mulOne('left') + pp.Optional(pp.oneOf('* /')('op') + mulOne('right')))
        addOne = pp.Group(mul('left') + pp.Optional(pp.oneOf('+ -')('op') + mul('right')))
        add = pp.Group(addOne('left') + pp.Optional(pp.oneOf('+ -')('op') + addOne('right')))
        compareExpr = pp.Group(add('left') + pp.Optional(pp.oneOf('> < == != >= <=')('op') + add('right')))
        expr << compareExpr('left') + pp.Optional(pp.oneOf('&& ||')('op') + compareExpr('right'))

        range = pp.Suppress('[') + expr + pp.Suppress(']')

        col = pp.Forward()

        subFields = pp.Group(col) + pp.ZeroOrMore(pp.Suppress('~') + pp.Group(col))
        compositeType = (pp.Suppress('{') + subFields('fields') + pp.Suppress('}'))('object')

        defVal = pp.Optional(pp.Suppress('=') + value('defVal'))
        atomType = (compositeType | identifier('type')) + pp.Optional(range('range')) + defVal
        array = atomType + pp.Optional(pp.Literal('*'))('array') + pp.Optional(range('arrayRange')) + defVal
        type = array | atomType

        typeDecl = type + pp.Optional(pp.ZeroOrMore(genQualifiers()))
        col << identifier('name') + pp.Optional(pp.Suppress(':') + typeDecl)

        self.col = col

    def parseColumn(self, s, tb=None):
        try:
            i = self.col.parseString(s, parseAll=True)
            i.table = tb
            TypeHandler.inst.onTypeParsed(i)
            return i
        except pp.ParseBaseException, err:
            raise ColumnParseError(s.split(':')[0], '%s:\n%s\n%s' % (err, err.line, " " * (err.column - 1) + '^'))

    @classmethod
    def eval_(cls, e):
        if isinstance(e, str):
            return e
        if e.op != '':
            return e.op, cls.eval_(e.left), cls.eval_(e.right)
        if e.left != '':
            return cls.eval_(e.left)


if __name__ == "__main__":
    TypeHandler()
    p = TypeParser()

    s = p.parseColumn('itemID: int=101')
    assert s.type == 'int'
    assert s.defVal == '101'

    s = p.parseColumn('itemID: int=101 *')
    assert s.type == 'int'
    assert s.defVal == '101'
    assert s.array == '*'

    s = p.parseColumn('itemID: int[value()>1]=101 * [sum()>1]')
    assert s.type == 'int'
    assert s.defVal == '101'
    assert s.array == '*'
    assert s.range <> ''
    assert s.arrayRange <> ''

    s = p.parseColumn('itemID: int key')
    assert s.key == 'key'
    assert s.unique == 'unique'
    assert s.type == 'int'

    s = p.parseColumn('itemID: int[min(1)] pk')
    assert s.pk == 'pk'
    assert s.unique == 'unique'
    assert s.type == 'int'
    assert s.range != ''

    s = p.parseColumn('itemID: int[1*value*2]')
    f = p.eval_(s.range)
    assert f == ('*', ('*', '1', 'value'), '2')

    s = p.parseColumn('itemID: int[1+value+2]')
    f = p.eval_(s.range)
    assert f == ('+', ('+', '1', 'value'), '2')

    s = p.parseColumn('itemID: int[1*value*2 + 3 + 4]')
    f = p.eval_(s.range)
    assert f == ('+', ('+', ('*', ('*', '1', 'value'), '2'), '3'), '4')

    s = p.parseColumn('ratio : {itemID:int[ref(item.itemID)]=101 ~ amount:int[min(1)]=1 ~ ratio:float[range(0,1)]}* [sum(ratio)<=(1+2)*3]')
    assert s.name == 'ratio'
    assert s.type == 'object'
    assert s.array == '*'
    assert len(s.fields) == 3
    assert s.fields[0].type == 'int'
    assert s.fields[0].defVal == '101'
    assert s.fields[0].range != ''
    assert s.arrayRange != ''

    s = p.parseColumn('accType: int map(accType.typeID)')
    assert s.map <> ''
