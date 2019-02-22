function appendHistory(type, query, uuid) {
    if (!uuid) return;
    if (type == 0) {
        // 用户消息
        $('.history').append(`
              <div class="right">
                 <div class="bubble-green">
                   <div class="bubble-avatar"><i class="fas fa-user"></i></div>
                   <p style="text-align: left" id="${uuid}">${query}</p>
                 </div>
              </div>
`);
    } else {
        $('.history').append(`
              <div class="left">
                 <div class="bubble-white">
                   <div class="bubble-avatar"><image src="./static/robot.png" width=32px attr="robot" /></div>
                   <p style="text-align: left" id="${uuid}">${query}</p>
                 </div>
              </div>
`);
    }
    $("#"+uuid).fadeIn(2000);
    var scrollHeight = $('.history').prop("scrollHeight");
    $('.history').scrollTop(scrollHeight, 200);
}

function getHistory () {
    $.ajax({
        url: '/gethistory',
        type: "GET",
        data: {'validate': getCookie('validation')},
        success: function(res) {            
            res = JSON.parse(res);
            if (res.code == 0) {
                historyList = JSON.parse(res.history);
                for (let i=0; i<historyList.length; ++i) {
                    h = historyList[i];
                    // 是否已绘制
                    if (!$('.history').find('#'+h['uuid']).length>0) {
                        appendHistory(h['type'], h['text'], h['uuid']);
                    }
                }
            } else {
                console.error('get history failed!');
            }            
        },
        error: function() {            
            console.error('get history failed!');
        }
    });
}

function autoRefresh( t ) {
    setInterval("getHistory();", t);
}

function upgrade() {
    $.ajax({
        url: '/upgrade',
        type: "POST",
        data: {'validate': getCookie('validation')},
        success: function(res) {
            $('.UPDATE-SPIN')[0].hidden = true;
            $('.UPDATE')[0].disabled = false;
            res = JSON.parse(res);
            if (res.code == 0) {
                toastr.success('更新成功，3秒后将自动重启')
                $('#updateModal').modal('hide')
                setTimeout(()=>{
                    location.reload();
                }, 3000);
            } else {
                toastr.error(res.message, '更新失败');
                $('#updateModal').modal('hide')
            }            
        },
        error: function() {
            
            toastr.error('服务器异常', '更新失败');
            $('#updateModal').modal('hide')
        }
    });
}

//用于生成uuid
function S4() {
    return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
}
function guid() {
    return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
}

$(function() {
    autoRefresh(5000);  // 每5秒轮询一次历史消息

    $('.CHAT').on('click', function(e) {
        e.preventDefault();
        var uuid = 'chat' + guid();
        var query = $("input#query")[0].value;
        appendHistory(0, query, uuid);
        $('input#query').val('');
        $.ajax({
            url: '/chat',
            type: "POST",
            data: {"type": "text", "query": query, "validate": getCookie("validation"), "uuid": uuid},
            success: function(res) {
                var data = JSON.parse(res);
                if (data.code == 0) {
                    toastr.success('指令发送成功');
                } else {
                    toastr.error(data.message, '指令发送失败');
                }
            },
            error: function() {
                toastr.error('服务器异常', '指令发送失败');
            }
        });
    });

    $('.UPDATE').on('click', function(e) {
        $('.UPDATE-SPIN')[0].hidden = false;
        $(this)[0].disabled = true;
        upgrade();
    });

    var scrollHeight = $('.history').prop("scrollHeight");
    $('.history').scrollTop(scrollHeight, 200);
});

