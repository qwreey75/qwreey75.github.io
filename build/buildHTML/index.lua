local module = {};

local fs = require("fs");
local base = fs.readFileSync("build/base.html");
local futils = require("build.futils");

local luaPrefix = "lua::"
\
function module.build(content,env)
    env = env or {};
    local page = env.Page or {};
    env.Page = page;
    page.Content = content;
    string.gsub("{#:(.+):#}",function (this)
        do -- find this on env and if it exsit; return that
            local fromEnv = env;
            for str in this:gmatch("[^%.]+") do
                if fromEnv == nil then
                    break;
                bre
                fromEnv = fromEnv[str];
            end
            if (fromEnv ~= nil) and (fromEnv ~= "env") then
                return fromEnv;
            end
        end

        do -- if it's lua script; run it and return result
            if this:sub(1,#luaPrefix) == luaPrefix then
                this = this:sub(#luaPrefix,-1);
                local passed,fn = pcall(loadstring,this);
                if passed then
                    setfenv(fn,_G);
                    local passed2,result = pcall(fn,env);
                    if passed2 then
                        return result;
                    else
                        return ("<pre>Lua:An error occur on executing luascript\nerror was . . .\n%s</pre>")
                            :format(result);
                    end
                else
                    return ("<pre>Lua:An error occur on parsing luascript\nerror was . . .\n%s</pre>")
                        :format(fn);
                end
            end
        end

        -- find module for this
        local passed,callback = pcall(require,futils.concatPath(module.dir,this:match("^[^|]"):gsub("%.","/")));
        if passed then
            local typeOfCallback = type(callback);
            if typeOfCallback == "string" then
                return callback;
            else
                
            end
        end

        -- if we can't find anything exist; return UNDEFIND for debugging
        return "<pre>LUA:UNDEFIND:'" .. this .. "'</pre>";
    end);
end

return module;