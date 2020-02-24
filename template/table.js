// AUTO GEN
<%def name="row(r,t)">
 {
  %for f, v in r.iteritems():
  %if t.fields[f].comment == '' and (t.fields[f].type=='' or v<>t.fields[f].defVal):
  ${f} : ${toJs(t,f,r.lineNo,v)},
  %endif
  %endfor
 }\
</%def>

%for t in tables:
// --------------------------------------------------------------------------------------------

let ${t.tableName} = {};
Cfg.${t.tableName} = ${t.tableName};

let default_${t.tableName} = {
 %for f, info in t.fields.iteritems():
 %if info.defVal.value<>'' or info.defVal[1].type=='str':
 ${f} : ${toJs(t,f,1,info.defVal)},
 %endif
 %endfor
};

%if t.key:
// key: ${t.key}
${t.tableName}.data = {
 %for r in t.data:
 [${toJs(t,t.key,r.lineNo,r[t.key])}] : ${row(r,t)},\
 %endfor

};

%else:
${t.tableName}.data = [
 %for r in t.data:
 ${row(r,t)},\
%endfor

];
%endif

for (let k in ${t.tableName}.data) {
    Object.setPrototypeOf(${t.tableName}.data[k], default_${t.tableName});
}

%for fName, i in t.fields.iteritems():
%if i.getter<>'':
${t.tableName}.findBy${fName[0].upper()+fName[1:]} = function(${fName}, nullable) {
    %if fName==t.key:
    let cfg = ${t.tableName}.data[${fName}];
    %else:
    let cfg = _.find(${t.tableName}.data,{${fName}:${fName}});
    %endif
    assert(nullable || cfg, 'No config in ${t.tableName} for ${i.name}: %s', ${fName});
    return cfg;
};

${t.tableName}.selectBy${fName[0].upper()+fName[1:]} = function(${fName}, nullable) {
    let cfgs = _.select(${t.tableName}.data,{${fName}:${fName}});
    assert(nullable || cfgs.length > 0, 'No config in ${t.tableName} for ${i.name}: %s', ${fName});
    return cfgs;
};
%endif
%endfor

${t.tableName}.find = function(predicate, nullable) {
    let cfg = _.find(${t.tableName}.data, predicate);
    assert(nullable || cfg, 'No config in ${t.tableName} for: %j', predicate);
    return cfg;
};

${t.tableName}.select = function(predicate, nullable) {
    let cfgs = _.select(${t.tableName}.data, predicate);
    assert(nullable || cfgs.length > 0, 'No config in ${t.tableName} for: %j', predicate);
    return cfgs;
};

${t.tableName}.map = function(predicate) {
    return _.map(${t.tableName}.data, predicate);
};

${t.tableName}.each = function(predicate) {
    _.each(${t.tableName}.data, predicate);
};

${t.tableName}.reduce = function(predicate, memo) {
    return _.reduce(${t.tableName}.data, predicate, memo);
};

${t.tableName}.pluck = function(key) {
    return _.pluck(${t.tableName}.data, key);
};

${t.tableName}.getArray = function() {
    if (!${t.tableName}.__dataArray)
        ${t.tableName}.__dataArray = _.values(${t.tableName}.data);
    return ${t.tableName}.__dataArray;
};

%endfor