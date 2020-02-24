from src.Generators.Generator import *


@gen
class LuaGen(Generator):
    def __init__(self):
        Generator.__init__(self)
        self.luaPath = appCfg['luaPath']

    @classmethod
    def escapeLuaKey(cls, k):
        if k in 'end for until function'.split() or re.match(r'\d+\w+', k):
            return "['%s']" % k
        return k

    @classmethod
    def dumpLua(cls, data):
        v, info = data
        if isinstance(v, list):
            return '{ %s }' % (', '.join(cls.dumpLua(vv) for vv in v))
        elif isinstance(v, dict):
            return '{' + ', '.join("%s=%s" % (cls.escapeLuaKey(k), cls.dumpLua(vv)) for k, vv in v.iteritems()) + '}'
        else:
            tp = TypeHandler.inst.types[info.type]
            if 'lua' in tp:
                return tp['lua'](v, info)
            return jsonEscape(v).decode('utf8')

    def generate(self, tables):
        self.logger.info('generating lua..')

        def toLua(t, f, l, v):
            try:
                return self.dumpLua(v)
            except:
                self.logger.error('lua gen failed at %s.%s, row %s, value: %s', t.tableName, f, l, v)
                raise

        files = set()
        genCnt = 0
        escapeLuaKey = self.escapeLuaKey
        tables = {k: v for k, v in tables.iteritems() if 'c' in v.mode}
        for wb, tables in groupBy(tables, lambda v: v.wb).iteritems():
            fBaseName = os.path.basename(wb.name).split('.')[0]
            fBaseName = fBaseName[0].upper() + fBaseName[1:]
            files.add(fBaseName)

            if wb.modified:
                tables.sort(key=lambda t: t.tableName)

                renderToFile(os.path.join(appCfg['cwd'], 'template/table.lua'), os.path.join(self.luaPath, fBaseName + '.lua'), locals())
                self.logger.debug('generated %s', fBaseName)
                genCnt += 1

        renderToFile(os.path.join(appCfg['cwd'], 'template/index.lua'), os.path.join(self.luaPath, 'Index.lua'), locals())
        self.logger.info('lua generating done: total %s files, gen:%s', len(files), genCnt)
