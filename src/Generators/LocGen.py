from src.Generators.Generator import *


@gen
class LocGen(Generator):
    def genLoc(self, tables):
        self.logger.info('generating localizations..')

        texts = OrderedDict()
        uniqueTexts = set()
        for tbName, tb in tables.iteritems():

            locFields = [fName for fName, f in tb.fields.iteritems() if f.type == 'loc']
            if not locFields:
                continue

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
                    if v not in uniqueTexts:
                        texts[key] = v
                        uniqueTexts.add(v)

        with file(appCfg['locPath'], 'w') as output:
            output.write('LocID,zh-CN\n')
            for k, v in texts.iteritems():
                output.write('%s,%s\n' % (u8encode(k), jsonEscape(v)))

        self.logger.info('localization generating done.')
