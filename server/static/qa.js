function upload() {
    $.ajax({
        url: '/qa',
        type: "POST",
        data: {"qa": $('#qa-input').val(), 'validate': getCookie('validation')},
        success: function(res) {
            var data = JSON.parse(res);
            if (data.code == 0) {
                toastr.success('提交成功');
            } else {
                toastr.error(data.message, '提交失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '设置失败');
        }
    });
}


$(function() {
    $('button#UPLOAD').on('click', function(e) {
        upload();
    });
});


$(document).delegate('#qa-input', 'keydown', function(e) {
    var keyCode = e.keyCode || e.which;

    if (keyCode == 9) {
        e.preventDefault();
        var start = this.selectionStart;
        var end = this.selectionEnd;

        // set textarea value to: text before caret + tab + text after caret
        $(this).val($(this).val().substring(0, start)
                    + "\t"
                    + $(this).val().substring(end));

        // put caret at right position again
        this.selectionStart =
            this.selectionEnd = start + 1;
    }
});
