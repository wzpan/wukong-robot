function saveConfig(msg) {
    if (window.location.href.indexOf('bot.hahack.com') >= 0) {
        bootbox.alert("demo 站点禁止修改配置!");
        return;
    }
    $.ajax({
        url: '/config',
        type: "POST",
        data: {"config": $('#config-input').val(), 'validate': getCookie('validation')},
        success: function(res) {
            var data = JSON.parse(res);
            if (!msg) msg='';
            if (data.code == 0) {
                toastr.success('设置成功'+msg);
            } else {
                toastr.error(data.message, '设置失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '设置失败');
        }
    });
}

$(function() {
    $.ajax({
        url: '/getconfig',
        type: "GET",
        data: {'validate': getCookie('validation')},
        success: function(res) {
            var data = JSON.parse(res);            
            if (data.code == 0) {
                let config = data.config;
                let sensitivity = data.sensitivity;
                if (config == '') {
                    $('#config-placeholder').append(`
    <center>
    <p> 找不到配置文件 <code>~/.wukong/config.yml</code> ，请先创建一份！</p>
    </center>
`);
                } else {
                    $('#config-placeholder').append(`
    <form class="form config-form" action="#">
    <div class="input-group" id="container">
      <div class="input-group-prepend">
        <span class="input-group-text">config.yml</span>
      </div>
        <textarea rows="20" class="form-control" id="config-input" placer='1' aria-label="With textarea">${config}</textarea>
    </div>
    <hr>
    <center>
    <button type="button" class="btn btn-primary mb-2" id="SAVE"><i class="fas fa-save"></i> 保存</button>&nbsp;
    <button type="button" class="btn btn-danger mb-2" data-toggle="modal" data-target="#restartModal"><i class="fas fa-power-off"></i> 重启</button>
    </center>
  </form>
`);
                }
                $('#sensitivitiy-value').text(sensitivity);
                $('input#sensitivitiy').val(parseFloat(sensitivity));
                $('input#sensitivity').on('input propertychange', function(e) {
                    e.preventDefault();
                    var value = $(this).val();
                    $('#sensitivitiy-value').text(value);
                });
                $('input#sensitivity').on('change', function(e) {
                    e.preventDefault();
                    var value = $(this).val();
                    var config = $('#config-input').val();
                    config.indexOf('')
                    var subStr=new RegExp('sensitivity: [0-9]+\.?[0-9]?')
                    result = config.replace(subStr, "sensitivity: " + value + " ");
                    $('#config-input').text(result);
                    saveConfig('，请重启生效');
                });
                $('button#RESTART').on('click', function(e) {
                    restart();
                });
                $('button#SAVE').on('click', function(e) {
                    saveConfig();
                });
            } else {
                toastr.error(data.message, '指令发送失败');
            }
        },
        error: function() {
            toastr.error('服务器异常', '指令发送失败');
        }
    });   
    
});

