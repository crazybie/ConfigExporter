# encoding=utf8

from src.Table import *
from src.GeneratorSys import *


class App:
    desc = u"""
#    Smart Excel Exporter    
#    【智能Excel导出工具】


--------------------------------    
# 例子:
```
    col : int = 0 notNull
    col : int [min(3)] *      int数组,元素最小为3
    col : int pk                            
    col : int pk key    
    col : int unique
    col : int [max(10)]
    itemID : uint [ref(items.itemID)] = 1001    
    col : { itemID :uint = 100 ~ amount :uint ~ ratio: float[range(0,1)] }* [sum(amount) < 10 && sum(ratio) <= 1]
```

- 支持指定客户端和服务器
    - 文件名字带@c表明生成客户端，带@s表明生成服务器
    - 可用外部excel导出工具输出到本工具的输入csv
    - 未带@的表也会解析（如枚举定义表），生成器可以判定是否需要生成
    
- 预处理
    - 支持复用列: 上一列: ^^, 左边一列：<<    
    - 支持单元格表达式格式化：列定义：level: int, power: int fmt,  然后power单元格内可以使用：{200 + level.value*5}
    - 支持字段映射：表A中：itemID: int map(itemDef.itemID), itemDef里面：itemName: str key, itemID: int
        即可在表A中填itemDef里面的itemName字符串，自动映射为itemDef里面的itemID
        

- 支持基础类型、复合类型和自定义类型
    - 参考--list命令行帮助
    - 支持自定义类型 loc,date
    - 支持指定自定义类型的输出方式
    - 支持别名，简化复合类型使用

- 支持类型修饰 unique,default,pk,key
    - default功能：指定type后若不指定值且无默认值则为type的默认值(int=0,float=0.0,str='',etc)
    - 参考--list命令行帮助

- 支持自定义check约束(range,ref,unique,sum)
    - 支持引用检查（ref）    
    - 支持约束表达式运算
    - 支持多列unique
    - 参考--list命令行帮助

- 支持导出多种格式
    - js和lua
    - 支持生成目标优化的结构：如lua利用元表做默认值
    - 支持生成母翻译（以loc指定）

"""

    def __init__(self):
        appCfg['__file__'] = __file__
        execfile(os.path.join(os.path.dirname(__file__), 'config.py'), appCfg)

        TypeHandler()
        TypeChecker(self, TypeHandler.inst)
        TypeParser()
        GeneratorSys()

        self.tables = OrderedDict()
        self.args = None
        self.wbCache = {}
        self.startTime = None

    def main(self):

        parser = argparse.ArgumentParser(description=self.desc, formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--list', action="store_true", help='list all types')
        parser.add_argument('--genDoc', action="store_true")
        parser.add_argument('--genLoc', action="store_true")
        parser.add_argument('--daemon', action="store_true")
        parser.add_argument('--logLevel', choices='DEBUG INFO WARN ERROR'.split(), default='INFO')
        self.args = parser.parse_args()

        if self.args.logLevel:
            L.getLogger().setLevel(self.args.logLevel)

        if self.args.list:
            s = StringIO()
            TypeHandler.inst.printHelp(s)
            print s.getvalue().decode('utf8')
            return

        if self.args.genDoc:
            with file(os.path.join(appCfg['cwd'], './doc/doc.md'), 'w') as f:
                f.write(u8encode(self.desc))
                f.write('\n-------- List命令行帮助 --------\n')
                s = StringIO()
                TypeHandler.inst.printHelp(s)
                f.write(s.getvalue())
            return

        if self.args.genLoc:
            self.exportLoc()
            return

        if self.args.daemon:
            self.daemon()
            return

        self.export()

    def exportLoc(self):
        try:
            startTime = datetime.datetime.now()

            for i in self.enumFiles():
                self.loadFile(i, enableChecking=False)
            L.info('loaded %s table' % len(self.tables))

            GeneratorSys.inst.genLoc(self.tables)
            L.info('export all took %s', datetime.datetime.now() - startTime)

        except Exception, e:
            traceback.print_exc()
            MessageBox('Error', e.message)

    def enumFiles(self):
        for i in walk(appCfg['csvDir'], '*.csv'):
            baseName = os.path.basename(i)
            if baseName.startswith('~$'):
                continue
            if i.count('.csv') == 2:
                continue  # merging temp files
            if '@' in baseName:
                mode = baseName.split('.')[0].split('@')[1]
                if mode not in ('cs', 'c', 's'):
                    continue
            yield i

    def beforeParseFileOnReloading(self):
        TypeChecker.inst.clearCache()

    def daemon(self):

        fileTimes = defaultdict(int)
        first = True

        while True:
            time.sleep(1)
            waitWindowClose('.*TortoiseGit')
            self.onStart()

            try:
                filesChanged = []
                existsFiles = []
                preHandle = False

                for i in self.enumFiles():
                    t = os.path.getmtime(i)
                    existsFiles.append(i)
                    if t > fileTimes[i]:
                        fileTimes[i] = t

                        if not preHandle:
                            preHandle = True
                            self.beforeParseFileOnReloading()

                        self.loadFile(i, checkDuplicated=False)
                        filesChanged.append((i, 'modified'))

                for k, v in fileTimes.items():
                    if k not in existsFiles:
                        filesChanged.append((k, 'removed'))
                        del fileTimes[k]
                        self.removeFileFromCache(k)

                if filesChanged:
                    if not first:
                        tip('\n'.join(i[1]+': '+os.path.basename(i[0]) for i in filesChanged))
                    self.onAllLoaded()

                first = False
            except Exception, e:
                traceback.print_exc()
                MessageBox('Error', e.message)

    def onAllLoaded(self):
        L.info('loaded %s table' % len(self.tables))
        self.genAll()

    def onStart(self):
        self.startTime = datetime.datetime.now()

    def export(self):
        try:
            self.onStart()

            L.info('loading files..')
            for i in self.enumFiles():
                self.loadFile(i)
                # break

            self.onAllLoaded()
        except Exception, e:
            traceback.print_exc()
            MessageBox('Error', e.message)

    def getTable(self, name):
        if name in self.tables:
            return self.tables[name]

        for f in self.enumFiles():
            simpleName = self.sheetName(f).split('@')[0]
            if simpleName == name:
                tb = self.loadFile(f)
                tb.preloaded = True

        return self.tables[name]

    @staticmethod
    def sheetName(fileName):
        return os.path.basename(fileName).split('.')[0]

    def loadFile(self, fileName, enableChecking=True, checkDuplicated=True):
        title = os.path.split(os.path.dirname(fileName))[1]
        sheetName = self.sheetName(fileName)

        if title not in self.wbCache:
            wb = Obj(name=title, sheets=[])
            self.wbCache[title] = wb
        else:
            wb = self.wbCache[title]
        wb.modified = True

        with file(fileName) as f:
            sheet = Obj(title=sheetName, rows=csv.reader(f))
            wb.sheets.append(sheetName)
            h = Table(self, wb, sheet, enableChecking=enableChecking)
            tName = h.tableName
            if checkDuplicated:
                if tName in self.tables and self.tables[tName].preloaded:
                    pass
                else:
                    assert tName not in self.tables, 'duplicated table: %s.%s, exists in: %s' % (h.wb.name, tName, self.tables[tName].wb.name)
            self.tables[tName] = h
        return h

    def removeFileFromCache(self, fileName):
        title = os.path.split(os.path.dirname(fileName))[1]
        sheetName = self.sheetName(fileName)

        wb = self.wbCache[title]
        wb.sheets.remove(sheetName)
        wb.modified = True
        if not wb.sheets:
            del self.wbCache[title]

        name, mode = Table.parseNameAndMode(sheetName)
        del self.tables[name]

        L.info('file not exists, remove from cache: %s', sheetName)

    def genAll(self):
        GeneratorSys.inst.genAll(self.tables)
        for k, v in self.tables.iteritems():
            v.wb.modified = False
        L.debug('export all took %s', datetime.datetime.now() - self.startTime)
        tip('all csv config generated')


if __name__ == '__main__':
    App().main()
