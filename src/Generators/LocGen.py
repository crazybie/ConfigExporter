from src.Generators.Generator import *


@gen
class LocGen(Generator):
    def genLoc(self, tables):
        self.logger.info('generating localizations..')

        texts = OrderedDict()
        for name, tb in tables.iteritems():
            locFields = [fName for fName, f in tb.fields.iteritems() if f.type == 'loc']
            for r in tb.data:
                for f in locFields:
                    key = '%s_%s_%s' % (name, f, r[tb.pk].value)
                    v, info = r[f]
                    texts[key] = v

        with file(appCfg['locPath'], 'w') as output:
            output.write('LocID,zh-CN\n')
            for k, v in texts.iteritems():
                output.write('%s,%s\n' % (u8encode(k), jsonEscape(v)))

        self.logger.info('localization generating done.')
