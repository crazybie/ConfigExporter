from src.Utils import *

configDir = r'..\..\Config'
os.chdir(configDir)


class CsvDialect(csv.excel):
    lineterminator = '\n'


def toValue(v):
    if isinstance(v, unicode):
        return v.encode('utf8')
    return v


for xlName in walk('.', '*.xlsx'):
    wb = openpyxl.load_workbook(xlName, data_only=True)
    for sh in wb.worksheets:
        outf = '%s/%s.csv' % (os.path.basename(xlName).split('.')[0], sh.title)
        makedir(outf)

        fields = [toValue(i.value) for i in sh.rows.next()]
        data = [{k: toValue(v.value) for k, v in zip(fields, row)} for row in sh.rows]
        csvOutF = csv.DictWriter(file(outf, 'w'), fields, dialect=CsvDialect)
        csvOutF.writeheader()
        csvOutF.writerows(data[1:])
        print sh.title
