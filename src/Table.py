from src.TypeParser import *
import src.CellHandler as ch


class Row(OrderedDict):
    def __init__(self, lineNo):
        self.lineNo = lineNo
        OrderedDict.__init__(self)


class Table:

    def __init__(self, app, wb, sheet, enableChecking=True):
        self.app = app
        self.preloaded = False
        self.sheet = sheet
        self.wb = wb
        self.uniqueCol = defaultdict(set)

        self.tableName, self.mode = Table.parseNameAndMode(sheet.title)

        self.data = []
        self.fields = {}
        self.fieldsList = []

        self.logger = L.getLogger(self.tableName)
        self.enableChecking = enableChecking

        self.logger.debug('loading data')
        self.rawData = [(idx + 1, [j for j in row]) for idx, row in enumerate(sheet.rows) if self.hasData(row)]

        self.parseFieldTypes()
        self.parseFieldsDefValue()
        self.parseData()

    @staticmethod
    def parseNameAndMode(title):
        if '@' in title:
            return title.split('@')
        else:
            return title, ''

    def hasData(self, row):
        for i in row:
            if i is not None and i <> '':
                return True
        return False

    def parseFieldTypes(self):
        self.logger.debug('parse fields')
        try:
            for i in self.rawData[0][1]:
                info = TypeParser.inst.parseColumn(i, self)
                info = TypeHandler.inst.processAlias(info, TypeParser.inst, self)
                self.fieldsList.append(info)

            self.fields = OrderedDict((f.name, f) for f in self.fieldsList)

        except ColumnParseError, e:
            self.logger.error('Column Error: %s, msg:\n%s', e.col, e.message)
            raise Exception('Table column parsing failed: %s.%s, msg: %s' % (self.tableName, e.col, e.message))

        except Exception, e:
            self.logger.error('parse type failed, %s', e.message)
            raise

    def getRow(self, line):
        for row in self.data:
            if row.lineNo == line:
                return row

    def parseData(self):
        self.logger.debug('parsing data')

        preRow = None
        fields = self.fields.keys()

        CellHandler = getattr(ch, self.tableName) if hasattr(ch, self.tableName) else ch.CellHandler

        class Context(dict, CellHandler):
            def __init__(self, d):
                dict.__init__(self, d)
                CellHandler.__init__(self)

        for lineNo, row in self.rawData[1:]:
            r = Row(lineNo)

            for idx, k, v in zip(range(len(fields)), fields, row):
                def func(v):
                    v = self.preprocessCell(k, v, idx, row, preRow, Context, r)
                    r[k] = TypeHandler.inst.parseData(v, self.fields[k], lineNo)

                self.try_(lineNo, k, func, v)

            self.data.append(r)
            preRow = row
            self.try_(lineNo, '', self.onRowParsed, r)

    def onRowParsed(self, r):
        if self.enableChecking:
            for f, info in self.fields.iteritems():
                v, info = r[f]

                def func():
                    if info.unique != '':
                        assert v not in self.uniqueCol[info.name], 'duplicated value %s' % v
                        self.uniqueCol[info.name].add(v)

                    TypeChecker.inst.checkValue(v, info, r.lineNo)

                self.try_(r.lineNo, f, func)

    def preprocessCell(self, k, v, idx, row, preRow, Context, r):
        if v == '^^' and preRow:
            v = row[idx] = preRow[idx]

        if v == '<<' and idx > 0:
            v = row[idx - 1]

        info = self.fields[k]
        if info.fmt <> '':
            ctx = Context(r)
            v = re.sub(r'\{(.*?)\}', lambda e: str(eval(e.group(1), ctx)), v)

        if info.map <> '':
            tb, col = info.map
            tb = self.app.getTable(tb)
            targetCells = [i[col] for i in tb.data if v == i[tb.key].value]
            assert targetCells, 'failed to map from %s=%s to %s' % (tb.key, v, col)
            v = targetCells[0].value

        return v

    def parseFieldsDefValue(self):
        for f, info in self.fields.iteritems():
            self.try_(1, info.name, self.parseFieldDefValue, info)

    def parseFieldDefValue(self, info):

        if info.fields <> '':
            for i in info.fields:
                self.parseFieldDefValue(i)

        if info.defVal <> '':
            if isinstance(info.defVal, CellData):
                # reuse other column by auto?
                pass
            else:
                info.defVal = TypeHandler.inst.parseData(info.defVal, info, 1)
        else:
            if info.array <> '':
                info.defVal = CellData([], info)
            elif info.type == 'object':
                info.defVal = CellData({}, info)
            else:
                info.defVal = CellData('', info)

    @property
    @cached
    def pk(self):
        d = [i.name for i in self.fields.values() if i.pk == 'pk']
        assert len(d) <= 1, 'Table should has only one `pk` field: %s, current: %s' % (self.tableName, d)
        return d[0] if d else None

    @property
    @cached
    def key(self):
        d = [i.name for i in self.fields.values() if i.key == 'key']
        assert len(d) <= 1, 'Table should has only one `key` field: %s, current: %s' % (self.tableName, d)
        return d[0] if d else None

    def try_(self, lineNo, field, cb, *args):
        try:
            return cb(*args)
        except Exception, e:
            traceback.print_exc()
            MessageBox('Error', 'Error in [%s.%s] at line %s, column "%s": %s, %s' % (self.wb.name, self.tableName, lineNo, field, type(e).__name__, e.message))
