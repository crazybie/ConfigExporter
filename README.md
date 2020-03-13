
    Smart Excel Exporter    
    【智能Excel导出工具】


--------------------------------    
# 例子:
`    col : int = 0 notNull
    col : int [min(3)] *      int数组,元素最小为3
    col : int pk                            
    col : int pk key    
    col : int unique
    col : int [max(10)]
    itemID : uint [ref(items.itemID)] = 1001    
    col : { itemID :uint = 100 ~ amount :uint ~ ratio: float[range(0,1)] }* [sum(amount) < 10 && sum(ratio) <= 1]
`

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


======= List命令行帮助 ======
      
Syntax：
    colDef => colName : type qualifiers
    type => typeDef [rangeExpression] = defaultValue
    typeDef => simpleType | { colDef ~ colDef ... } | type *    
    simpleType => int | float | str ...
    *: array
        
======= types =========
int       : <no doc>
	 default: 0
auto      : reuse type of other column(can cross table), e.g. col: auto typeof(<otherTable.>col)
uint      : unsigned int
	 default: 0
bool      : true: 1 or true; false: 0 or false
	 default: false
float     : <no doc>
	 default: 0.0
str       : <no doc>
	 default: 
object    : parse to user defined structure, usage: {f1:type ~ f2:type} [rangeCheckers]

=== Custom types ===:
loc       : str that will be generated with localization function call, eg. T("")
	MUST have a pk field
dateBegin : string like "2018.11.1", output js: new Date("2018.11.1 00:00:00")
dateEnd   : string like "2018.11.1", output js: new Date("2018.11.1 23:59:59")

===== qualifiers ======
pk        : has [unique, getter] attribute, primary unique id of one row, one table should has only one pk column
key       : has [unique, getter] attribute, generate as a map with this filed as key
unique    : has [notNull] attribute, unique in this table
notNull   : should not be empty
getter    : generate checked getter function
fmt       : can use fmt expression
comment   : wont generate anything
map(table.col): map to another table's column
typeof(table.col): use with auto to map to another table's column

===== type alias ======
item      : item: itemID ~ itemAmount
audio     : audio: eventName ~ volume
scope     : scope: min ~ max
icon      : str value, for icon prefabs under Assets\Builds\UI\UITexture
itemID    : itemID in items table
optionalItemID: itemID in items table

======= range functions =========
fileExists:
	usage:
        fileExists('Assets/Builds/UI/'+value()+'.prefab')
        wont check empty str. 

fileExistsUnder:
	usage:
                fileExistsUnder('Assets/Builds/UI/',value()+'.prefab')
                wont check empty str. 

floatEq   :
	no doc

len       :
	usage:
        len()>0 or
        len(field)>0 for object type

max       :
	usage: max(100)
        check if value is less than or equal to 100

min       :
	usage: min(0)
        check if value is lager than or equal to 0

range     :
	usage: range(0,100)
        check if value is in range[min,max]

ref       :
	usage: ref(table.columnName)
        check if value is in target column of table

refWhenNotNull:
	usage: refWhenNotNull(table.columnName)
        like ref but only do check when value is not null.

sum       :
	usage: sum(fieldName)
        return sum of specify field of the array
        

unique    :
	multiple columns as a unique key,
        usage: itemID : int [unique(skillID)], unique key using (itemID, skillID).
        

value     :
	usage:
        value()>0 or
        value(field)>0 for object type

