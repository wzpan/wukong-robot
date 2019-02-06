function getHistory () {
    $.ajax({
        url: '/history',
        type: "GET",
        success: function(res) {
            res = JSON.parse(res);
            if (res.code == 0) {
                historyList = JSON.parse(res.message);
                for (let i=0; i<historyList.length; ++i) {
                    h = historyList[i];
                    // 是否已绘制
                    if (!$('.history').find('#'+h['uuid']).length>0) {
                        if (h['type'] == 0) {
                            // 用户消息
                            $('.history').append(`
              <div class="right">
                 <div class="bubble-green">
                   <div class="bubble-avatar"><i class="fas fa-user"></i></div>
                   <p style="text-align: left" id="${h['uuid']}">${h['text']}</p>
                 </div>
              </div>
`);
                        } else {
                            $('.history').append(`
              <div class="left">
                 <div class="bubble-white">
                   <div class="bubble-avatar"><i class="fas fa-user"></i></div>
                   <p style="text-align: left" id="${h['uuid']}">${h['text']}</p>
                 </div>
              </div>
`);
                        }
                        $("#"+h['uuid']).fadeIn(1000);
                        var scrollHeight = $('.history').prop("scrollHeight");
                        $('.history').scrollTop(scrollHeight, 200);
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

$(function() {
    autoRefresh(5000);  // 每5秒轮询一次历史消息
});
