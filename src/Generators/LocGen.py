from src.Generators.Generator import *


@gen
class LocGen(Generator):
    def genLoc(self, tables):
        self.logger.info('generating localizations..')

        texts = OrderedDict()
        for tbName, tb in tables.iteritems():
            if tbName in appCfg['csvLocFiles']:
                singleFileTexts = OrderedDict()
                self.genOneLoc(tb, tbName, singleFileTexts)
                self.outputLoc('%s\%s.csv' % (appCfg['locPath'], tbName), singleFileTexts)
            else:
                self.genOneLoc(tb, tbName, texts)

        self.outputLoc('%s\csv.csv' % appCfg['locPath'], texts)
        self.logger.info('localization generating done.')

    def genOneLoc(self, tb, tbName, texts):

        locFields = [fName for fName, f in tb.fields.iteritems() if f.type == 'loc']
        if not locFields:
            return

        locKeyFields = [fName for fName, f in tb.fields.iteritems() if f.locKey == 'locKey' or f.pk == 'pk']
        assert locKeyFields, 'need pk or locKey column for table: %s' % (tbName,)

        uniqueLocKeys = set()
        for r in tb.data:

            locKey = tuple(str(r[i].value) for i in locKeyFields)
            assert locKey not in uniqueLocKeys, 'loc key not unique. table:%s, row:%s' % (tbName, r.lineNo)
            uniqueLocKeys.add(locKey)

            for f in locFields:
                key = '_'.join([tbName, f] + list(locKey))
                v, info = r[f]
                if v not in texts.itervalues():
                    texts[key] = v

    def outputLoc(self, out, texts):
        with file(out, 'w') as output:
            output.write('LocID,zh-CN\n')
            for k, v in texts.iteritems():
                output.write('%s,%s\n' % (u8encode(k), jsonEscape(v)))
        self.logger.debug('localization %s generated.', out)
