var md = window.markdownit({
    html: true,
    linkify: true,
    typographer: true,
    highlight: function (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return '<pre class="hljs"><code>' +
                 hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                 '</code></pre>';
        } catch (__) {}
      }
  
      return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';  
    }
  });

function appendHistory(type, message, uuid, plugin) {
    if (!uuid) return;
    if (type == 0) {
        // 用户消息
        $('.history').append(`
              <div class="right">
                 <div class="bubble bubble-green">
                   <div class="bubble-text" id="${uuid}">${message}</div>
                 </div>
              </div>
`);
    } else {
        messages = message.split('\n');
        $('.history').append(`
          <div class="left">
             <div class="bubble bubble-white">
               <div class="bubble-text" id="${uuid}"></div>
             </div>
           </div>
        `);
        $(`#${uuid}`).append(md.render(`${message}`));
        if (plugin) {
            $(`#${uuid}`).after(`
               <span class="badge badge-info plugin">${plugin}</span>
            `);
        }
    }
    $("#"+uuid).hide();
    $("#"+uuid).fadeIn(500, ()=>{
        var scrollHeight = $('.history').prop("scrollHeight");
        $('.history').scrollTop(scrollHeight, 200);
    });
}

function showProgress() {
    progressJs().increase();
}

function upgrade() {
    var args = {'validate': getCookie('validation')}
    $.ajax({
        url: '/upgrade',
        type: "POST",
        data: $.param(args),        
        success: function(res) {
            $('.UPDATE-SPIN')[0].hidden = true;
            $('.UPDATE')[0].disabled = false;
            res = JSON.parse(res);
            if (res.code == 0) {
                toastr.success('更新成功，5秒后将自动重启')
                
                $('#updateModal').modal('hide')
                progressJs().start();
                setInterval("showProgress()", 1000);
                setTimeout(()=>{
                    progressJs().end();
                    clearInterval();
                    location.reload();
                }, 5000);
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

// 创建WebSocket连接
var socket = new WebSocket("ws://" + location.host + "/websocket");

// 监听WebSocket打开事件
socket.onopen = function (e) {
    console.log("WebSocket连接已打开");
};

// 监听WebSocket关闭事件
socket.onclose = function (e) {
    console.log("WebSocket连接已关闭");
};

var rawData = {}

var showMessage = function(data) {
    var existing = $("#" + data.uuid);
    if (existing.length > 0) {
        // 如果存在，追加内容，并重新用 markdown 渲染
        if (rawData[data.uuid] == undefined) {
            rawData[data.uuid] = data['text'];
        } else {
            rawData[data.uuid] += data['text'];
        }
        $(`#${data.uuid}`)[0].innerHTML = md.render(rawData[data.uuid]);
    } else {
        rawData[data.uuid] = data['text'];
        appendHistory(data['type'], data['text'], data['uuid'], data['plugin']);
    }
}

// 监听WebSocket消息事件
socket.onmessage = function (e) {
    var data = JSON.parse(e.data);
    if (data.action === "new_message") {
        // console.log("收到新消息: ", data);
        showMessage(data)
        let scrollHeight = $('.history').prop("scrollHeight");
        $('.history').scrollTop(scrollHeight, 200);
    }
};

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};
    $('.CHAT').on('click', function(e) {
        e.preventDefault();
        var disabled = $('#query');
        disabled.disable();
        var uuid = 'chat' + guid();
        var query = $("input#query")[0].value;
        if (query.trim() == '') {
            toastr.error('请输入有效的命令');
            return;
        }
        appendHistory(0, query, uuid);
        $('input#query').val('');
        var args = {"type": "text", "query": query, 'validate': getCookie('validation'), "uuid": uuid}
        $.ajax({
            url: '/chat',
            type: "POST",
            data: $.param(args),
            success: function(res) {
                disabled.enable();
                if (!res) return;
                var data = JSON.parse(res);
                if (data.code == 0) {
                    toastr.success('指令发送成功');
                } else {
                    toastr.error(data.message, '指令发送失败');
                }
            },
            error: function() {
                disabled.enable();
                toastr.error('服务器异常', '指令发送失败');
            }
        });
    });


    $('.UPDATE').on('click', function(e) {
    $('.UPDATE-SPIN')[0].hidden = false;
       $(this)[0].disabled = true;
       upgrade();
    });

    updater.poll();
});


jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};

var updater = {
    errorSleepTime: 500,
    cursor: null,

    poll: function() {
        console.log('updater poll');
        var args = {'validate': getCookie('validation')}        
        if (updater.cursor) args.cursor = updater.cursor;
        $.ajax({
            url: '/chat/updates',
            type: "POST",
            data: $.param(args),
            success: updater.onSuccess,
            error: updater.onError
        });        
    },

    onSuccess: function(response) {
        console.log("updater poll success")
        try {
            var res = JSON.parse(response);            
            updater.newMessages(res);
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        updater.errorSleepTime *= 2;
        console.error("get history failed! sleeping for", updater.errorSleepTime, "ms");
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newMessages: function(response) {
        if (response.code != 0 || !response.history) return;
        var messages = JSON.parse(response.history);
        updater.cursor = messages[messages.length - 1].uuid;
        console.log(messages.length, "new messages, cursor:", updater.cursor);
        for (var i = 0; i < messages.length; i++) {
            updater.showMessage(messages[i]);
        }
    },

    showMessage: function(message) {
        var existing = $("#" + message.uuid);
        if (existing.length > 0) return;
        appendHistory(message['type'], message['text'], message['uuid'], message['plugin']);
    }
};
