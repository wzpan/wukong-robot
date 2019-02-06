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
