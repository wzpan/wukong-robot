$(function() {
 
    $('.LOGIN').on('click', function(e) {
        e.preventDefault();
        var username = $("input#username")[0].value;
        var password = $("input#password")[0].value;
        args = {'username': username, "password": password}
        $.ajax({
            url: '/login',
            type: "POST",
            data: args,
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

