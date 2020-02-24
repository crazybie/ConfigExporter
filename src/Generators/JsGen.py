from src.Generators.Generator import *


@gen
class JsGen(Generator):

    def __init__(self):
        Generator.__init__(self)
        self.jsPath = appCfg['jsPath']

    @classmethod
    def dumpJs(cls, data):
        v, info = data
        if isinstance(v, list):
            return '[ %s ]' % (', '.join(cls.dumpJs(vv) for vv in v))
        elif isinstance(v, dict):
            return '{' + ', '.join("%s: %s" % (k, cls.dumpJs(vv)) for k, vv in v.iteritems()) + '}'
        else:
            tp = TypeHandler.inst.types[info.type]
            if 'js' in tp:
                return tp['js'](v, info)
            return jsonEscape(v).decode('utf8')

    def generate(self, tables):
        self.logger.info('generating js..')

        def toJs(t, f, l, v):
            try:
                return self.dumpJs(v)
            except:
                self.logger.error('js gen failed at %s.%s, row %s, value: %s', t.tableName, f, l, v)
                raise

        files = set()
        genCnt = 0
        tables = {k: v for k, v in tables.iteritems() if 's' in v.mode}
        for wb, tables in groupBy(tables, lambda v: v.wb).iteritems():
            fBaseName = os.path.basename(wb.name).split('.')[0]
            files.add(fBaseName)

            if wb.modified:
                tables.sort(key=lambda t: t.tableName)

                renderToFile(os.path.join(appCfg['cwd'], 'template/table.js'), os.path.join(self.jsPath, fBaseName + '.js'), locals())
                self.logger.debug('generated %s', fBaseName)
                genCnt += 1

        renderToFile(os.path.join(appCfg['cwd'], 'template/index.js'), os.path.join(self.jsPath, 'index.js'), locals())
        self.logger.info('js generating done: total %s files, gen:%d', len(files), genCnt)
