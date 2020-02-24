-- AUTO GEN

<%def name="row(r,t)">
 {
  %for f, v in r.iteritems():
  %if t.fields[f].comment == '' and (t.fields[f].type=='' or v<>t.fields[f].defVal):
   ${escapeLuaKey(f)} = ${toLua(t,f,r.lineNo,v)},
  %endif
  %endfor
 }\
</%def>

%for t in tables:
--------------------------------------------------------------------------------------------

local ${t.tableName} = {}
Cfg.${t.tableName} = ${t.tableName}

---@class ${t.tableName}
local default_${t.tableName} = {
 %for f, info in t.fields.iteritems():
 %if t.fields[f].comment == '':
 ${escapeLuaKey(f)} = ${toLua(t,f,1,info.defVal)},
 %endif
 %endfor
}
default_${t.tableName}.__index = default_${t.tableName}

%if t.key:
-- key: ${t.key}
${t.tableName}.data = {
 %for r in t.data:
 [${toLua(t, t.key, r.lineNo, r[t.key])}] = ${row(r,t)},\
 %endfor

}
%else:
${t.tableName}.data = {
 %for r in t.data:
 ${row(r,t)},\
 %endfor

}
%endif

for _,v in pairs(${t.tableName}.data) do
    setmetatable(v, default_${t.tableName})
end

%for fName, i in t.fields.iteritems():
%if i.getter<>'':

---@return ${t.tableName}
function ${t.tableName}.FindBy${fName[0].upper()+fName[1:]}(${fName}, nullable)
    %if fName == t.key:
    local cfg = ${t.tableName}.data[${fName}]
    %else:
    local cfg = _.find(${t.tableName}.data,{${fName}=${fName}})
    %endif
    assert(nullable or cfg, 'No config in ${t.tableName} for ${i.name}: %s', ${fName})
    return cfg
end

---@return ${t.tableName}[]
function ${t.tableName}.SelectBy${fName[0].upper()+fName[1:]}(${fName}, nullable)
    local cfgs = _.select(${t.tableName}.data,{${fName}=${fName}})
    assert(nullable or #cfgs > 0, 'No config in ${t.tableName} for ${i.name}: %s', ${fName})
    return cfgs
end
%endif
%endfor

---@param predicate fun(i:${t.tableName})
---@return ${t.tableName}
function ${t.tableName}.Find(predicate, nullable)
    local cfg = _.find(${t.tableName}.data, predicate)
    assert(nullable or cfg, 'No config in ${t.tableName} for: %s', tostring_auto(predicate))
    return cfg
end

---@param predicate fun(i:${t.tableName})
---@return ${t.tableName}[]
function ${t.tableName}.Select(predicate, nullable)
    local cfgs = _.select(${t.tableName}.data, predicate)
    assert(nullable or #cfgs > 0, 'No config in ${t.tableName} for: %s', tostring_auto(predicate))
    return cfgs
end

---@param predicate fun(i:${t.tableName})
---@return ${t.tableName}[]
function ${t.tableName}.Map(predicate)
    return _.map(${t.tableName}.data, predicate)
end

---@param predicate fun(i:${t.tableName})
function ${t.tableName}.Each(predicate)
    _.each(${t.tableName}.data, predicate)
end

---@generic M
---@param predicate fun(memo:M, i:${t.tableName})
---@param memo M
---@return M
function ${t.tableName}.Reduce(predicate, memo)
    return _.reduce(${t.tableName}.data, predicate, memo)
end

function ${t.tableName}.Pluck(key)
    return _.pluck(${t.tableName}.data, key)
end

---@return ${t.tableName}[]
function ${t.tableName}.GetArray()
    if not ${t.tableName}.__dataArray then
        ${t.tableName}.__dataArray = _.values(${t.tableName}.data)
    end
    return ${t.tableName}.__dataArray
end

%endfor