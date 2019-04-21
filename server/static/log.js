function refresh(msg) {
    $.ajax({
        url: '/getlog',
        type: "GET",
        data: $.param({'validate': getCookie('validation')}),
        success: function(res) {
            var data = JSON.parse(res);            
            if (data.code == 0) {
                let log = data.log;
                $('#log-input').text(log);
                var scrollHeight = $('#log-input').prop("scrollHeight");
                $('#log-input').scrollTop(scrollHeight, 200);
                $('button#REFRESH').on('click', function(e) {
                    refresh();
                });
            } else {
                toastr.error(data.message, '日志读取失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '日志读取失败');
        }
    });   
}

$(function() {
    refresh();
});

