var menu = document.getElementById('menu');

function renderMenu() {
	menu.style.display = 'none';
	setTimeout(function() {
	    menu.style.display = 'block';
	    menu.className = 'mfb-component--br'; + 'mfb-zoomin';
	},1);
};
