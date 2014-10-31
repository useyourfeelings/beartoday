function bbsOnClick(event, treeId, treeNode) {
    window.location.href="/bbs/" + treeNode.name; 
}

function BBSTREE(id){
    this.bbs_id = id;
    
    this.bbstreesetting = {
        edit: {
            drag: {
                isMove: false,
                isCopy: false,
                autoOpenTime: 0
            }
        },
        view: {
            showIcon: false,
            selectedMulti: false
        },
        data: {
            simpleData: {
                enable: true,
                rootPId: 0
            },
            keep: {
                parent:true,
                leaf:true
            },
        },
        check: {
            enable: false
        },
        callback: {
            onClick:bbsOnClick,
        }
    };
    
    this.getbbstree = function(){
        var me = this;
        
        function getbbstreeover(data, status){
            if(status == "success")
            {
                var data_parsed = JSON.parse(data);
                $.fn.zTree.init($("#bbstree"), me.bbstreesetting, data_parsed);
                var treeObj = $.fn.zTree.getZTreeObj("bbstree");
                treeObj.expandAll(true);
                
                nodes = treeObj.getNodesByParam("id", me.bbs_id);
                treeObj.selectNode(nodes[0]);
            }
            else
            {
                alert("something wrong, a refresh is needed.^_^\"");
            }
        }
        
        $.post("/getbbstree", {}, getbbstreeover);
    };
}