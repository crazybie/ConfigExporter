from src.Utils import *

cwd = os.path.join(os.path.dirname(__file__))

csvDir = os.path.join(cwd, "../../Config")

clientRoot = os.path.abspath(os.path.join(cwd, r'..\..\\'))
serverRoot = os.path.join(clientRoot, '..\\', clientRoot.split('\\')[-1].replace('client', 'server'))
luaPath = os.path.join(clientRoot, r'Assets\Lua\Config')
jsPath = os.path.join(serverRoot, r'game-server\app\config')
locPath = os.path.join(clientRoot, r'Localization\zh-CN')
csvLocFiles = 'skill dialogueData tipData items skillInitiativeData skillBasicData'.split()

#######################################################
# custom types

customTypes = [
    {
        'token': 'loc',
        'doc': 'str that will be generated with localization function call, eg. T("")\n\tMUST have a pk field',
        'simpleType': True,
        'lua': lambda x, i: ('T(%s)' % jsonEscape(x)).decode('utf8'),
        'js': lambda x, i: ('utils.loc(%s)' % jsonEscape(x)).decode('utf8'),
    },
    {
        'token': 'dateBegin',
        'doc': 'string like "2018.11.1", output js: new Date("2018.11.1 00:00:00")',
        'simpleType': True,
        'js': lambda x, i: 'new Date("%s 00:00:00")' % x,
    },
    {
        'token': 'dateEnd',
        'doc': 'string like "2018.11.1", output js: new Date("2018.11.1 23:59:59")',
        'simpleType': True,
        'js': lambda x, i: 'new Date("%s 23:59:59")' % x,
    },
]

typeAlias = [
    {
        "token": "item",
        "doc": "item: itemID ~ itemAmount",
        "type": "{itemID: uint[ref(items.itemID)] ~ itemAmount: uint=1}"
    },
    {
        "token": "audio",
        "doc": "audio: eventName ~ volume",
        "type": "{eventName: str~ volume: float = 1}"
    },
    {
        "token": "scope",
        "doc": "scope: min ~ max",
        "type": "{min: float ~ max: float}"
    },
    {
        "token": "icon",
        "doc": "str value, for icon prefabs under Assets\Builds\UI\UITexture",
        "type": "str [fileExistsUnder('Assets\Builds\UI\UITextures', value()+'.prefab')]"
    },
    {
        "token": "itemID",
        "doc": "itemID in items table",
        "type": "uint[ref(items.itemID)]"
    },
    {
        "token": "optionalItemID",
        "doc": "itemID in items table",
        "type": "uint[refWhenNotNull(items.itemID)]"
    }
]
