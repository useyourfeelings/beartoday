var editor = ace.edit("markdown_editor");
var mdi = new MDI(editor);
var converter = new Markdown.getSanitizingConverter();
var previewHtml = '';

function makePreview(){
    previewHtml = converter.makeHtml(mdi.getWholeText())
    $('#markdown_preview').html('<div class="ui stacked segment">' + previewHtml + '</div>');
    $('pre code').each(function(i, block) {
        hljs.highlightBlock(block);
    });
}

function onChange(){
    makePreview();
    mdi.saveStorageState();
}

mdi.setUseWrapMode(true);
mdi.setShowPrintMargin(false);
mdi.setFontSize(16);
mdi.setTheme("ace/theme/chrome");
mdi.setMode("ace/mode/markdown");
mdi.loadStorageState();

mdi.focus();
mdi.setOnChangeCallback(onChange);

makePreview();

$('#undo').click(function(){
    mdi.undo();
});

$('#redo').click(function(){
    mdi.redo();
});

$('#dobold').click(function(){
    mdi.doBold();
});

$('#addurl').click(function(){
    mdi.addUrl();
});

$('#addimg').click(function(){
    mdi.addImage();
});

$('#newdoc').click(function(){
    mdi.newDoc();
});

$('#exporthtml').click(function(){
    text = $('#markdown_preview').html();
    var blob = new Blob([text], {type: "text/plain;charset=utf-8"});
    saveAs(blob, "untitled.html");
    mdi.focus();
});

$('#exportmd').click(function(){
    text = mdi.getWholeText();
    var blob = new Blob([text], {type: "text/plain;charset=utf-8"});
    saveAs(blob, "untitled.md");
    mdi.focus();
});

$('#help').click(function(){
    mdi.focus();
})

function onSplitterDargEnd() {
    mdi.resize();
}



