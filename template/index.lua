-- AUTO GEN
local this = {}
Cfg = {}

this.Load = function()
    %for f in sorted(files):
    require('Config.${f}')
    %endfor
end

return this