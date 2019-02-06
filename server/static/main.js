var menu = document.getElementById('menu');

function renderMenu() {
	menu.style.display = 'none';
	setTimeout(function() {
	    menu.style.display = 'block';
	    menu.className = 'mfb-component--br'; + 'mfb-zoomin';
	},1);
};


function getCookie(name)
{
    var arr,reg=new RegExp("(^| )"+name+"=([^;]*)(;|$)");
    if(arr=document.cookie.match(reg))
        return unescape(arr[2]);
    else
        return null;
}

//写cookies
function setCookie(name,value)
{
    var Days = 30;
    var exp = new Date();
    exp.setTime(exp.getTime() + Days*24*60*60*1000);
    document.cookie = name + "="+ escape (value) + ";expires=" + exp.toGMTString();
}

function arrayBufferToBase64( buffer ) {
    var binary = '';
    var bytes = new Uint8Array( buffer );
    var len = bytes.byteLength;
    for (var i = 0; i < len; i++) {
        binary += String.fromCharCode( bytes[ i ] );
    }
    return window.btoa( binary );
}

$(function() {
    var recorder = new Recorder({
        monitorGain: 0,
        recordingGain: 1,
        numberOfChannels: 1,
        wavBitDepth: 16,
        encoderPath: "./static/waveWorker.min.js"
    });

    this.recording = false;
    var start = $("a#start-record");
    var stop = $("a#stop-record");

    stop.on('click', (e) => {
        if (!this.recording) return;
        this.recording = false;
        recorder.stop();
    });

    start.on('click', (e) => {
        if (this.recording) return;
        this.recording = true;
        if (!Recorder.isRecordingSupported()) {
            toastr.error("您的浏览器不支持录音", '录音失败');
            return;
        }
        recorder.start().catch(function(e){
            toastr.error(e.message, '录音失败');
        });

        recorder.onstart = function(){
          console.debug('Recorder is started');
          start.disabled = true;
          stop.disabled = false;
        };

        recorder.onstop = function(){
          console.debug('Recorder is stopped');
          start.disabled = false;
          stop.disabled = true;
        };

        recorder.onstreamerror = function(e){
          console.error('Error encountered: ' + e.message );
        };

        recorder.ondataavailable = function( typedArray ){
            data = arrayBufferToBase64(typedArray);
            $.ajax({
                url: '/chat',
                type: "POST",
                data: {"type": "voice", "voice": data, "validate": getCookie("validation")},
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
        };
    });
});
