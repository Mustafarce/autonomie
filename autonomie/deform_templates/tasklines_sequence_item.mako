# -*- coding: utf-8 -*-
%if field.error:
    <div class='row taskline' id="${field.oid}">
    %else:
        <div class='row taskline' id="${field.oid}">
    %endif
    ${field.serialize(cstruct)|n}
    <div class='span1'>
        <button type='button' class='close' onclick="$(this).parent().parent().remove();$(Facade).trigger('linedelete');">x</button>
    </div>
</div>

