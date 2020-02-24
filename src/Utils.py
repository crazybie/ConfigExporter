import json, sys, os, re, time, csv, traceback, ctypes, shutil, datetime, ctypes, operator, inspect, argparse, functools
from collections import *
from cStringIO import StringIO
import logging as L
from WindowsBalloonTip import *
from win32gui import *

def installPackage(name):
    os.system('%s -m pip install %s' % (sys.executable, name))


try:
    import openpyxl
except:
    installPackage('openpyxl')
    import openpyxl

try:
    import pyparsing as pp
except:
    installPackage('pyparsing')
    import pyparsing as pp

try:
    import mako
    from mako.template import Template
except:
    installPackage('mako')
    import mako
    from mako.template import Template

######################################################################

L.basicConfig(level=L.INFO, format='%(asctime)s:[%(levelname)-5s]:[%(name)-24s] %(message)s')
appCfg = {}


def assertExpr(b, msg):
    assert b, msg
    return b


def getFuncArgCount(p):
    args = inspect.getargspec(p)[0]
    argsCnt = len(args)
    if args[0] == 'self': argsCnt -= 1
    return argsCnt


def findOne(data, **kw):
    def key(i):
        for k, v in kw.iteritems():
            if i[k] != v:
                return False
        return True

    return filter(key, data)[0]


def cached(f):
    memo = {}

    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = f(*args)
            memo[args] = rv
            return rv

    return wrapper


def jsonEscape(s):
    return json.dumps(s, ensure_ascii=False)


def u8decode(s):
    if isinstance(s, unicode):
        return s
    return s.decode('utf8')


def u8encode(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s


def MessageBox(title, msg):
    ctypes.windll.user32.MessageBoxW(None, unicode(msg), unicode(title), 0x10 | 4096)


def walk(p, wildChar=None):
    """

    :type wildChar: str
    :type p: str
    """
    import fnmatch
    for r, dirs, files in os.walk(p):
        if wildChar:
            for f in fnmatch.filter(files, wildChar):
                yield r + '/' + f
        else:
            for f in files:
                yield r + '/' + f


class Obj:
    def __init__(self, **kargs):
        self.__dict__.update(kargs)


def iterateValue(data):
    """

    :type data: []|{}
    """
    if isinstance(data, (list, tuple)):
        for v in data:
            yield v
    elif isinstance(data, dict):
        for k, v in data.iteritems():
            yield v


def groupBy(data, keyFn):
    """

    :type keyFn: Callable(Any)
    :type data: {}|[]
    """
    grouped = OrderedDict()

    for v in iterateValue(data):
        kk = keyFn(v)
        if kk in grouped:
            grouped[kk].append(v)
        else:
            grouped[kk] = [v]
    return grouped


def makedir(p):
    p = os.path.dirname(p)
    if not os.path.exists(p):
        os.makedirs(p)


def renderToFile(tempFile, outputFile, context):
    """

    :type context: {}
    :type outputFile: str
    :type tempFile: str
    """
    data = renderToStr(file(tempFile).read(), context)
    makedir(outputFile)
    file(outputFile, 'w').write(data)


def renderToStr(temp, context):
    """

    :type context: {}
    :type temp: str
    """
    try:
        if 'self' in context:
            del context['self']
        context['jsonDumps'] = lambda *args, **kwargs: json.dumps(*args, ensure_ascii=False, sort_keys=False, **kwargs)
        return Template(temp).render_unicode(**context).encode('utf8')
    except:
        raise Exception(mako.exceptions.text_error_template().render())


def updateFileSection(fileName, tag, tempStr, context, comment='//'):
    tag = '%s %s' % (comment, tag)
    new = '%s {\n' % tag + renderToStr(tempStr, context) + '%s }' % comment
    if not os.path.isfile(fileName):
        makedir(fileName)

    s = file(fileName).read()
    m = re.search(r'(%s \{.*?%s \})' % (tag, comment), s, flags=re.DOTALL)
    if m:
        s = s.replace(m.group(0), new)
    else:
        s += '\n\n' + new
    file(fileName, 'w').write(s)
    L.info('file section %s updated' % fileName)


def getTopWindowTitle():
    return GetWindowText(GetForegroundWindow())
    
def isWindowOnTop(titleRe):
    t = getTopWindowTitle()
    return re.match(titleRe, t)<>None
    
def waitWindowClose(titleRe, sleepSec=2):
    while isWindowOnTop(titleRe):
        time.sleep(sleepSec)
        print titleRe,'is on top, waiting.'