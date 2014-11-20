var isSelected = false;

function bind_click(){
	var valid_list = document.getElementsByClassName('valid');
	var inputSelect = document.getElementById('input');
	for (var i = 0; i < valid_list.length; i++) {
		valid_list[i].onclick = function (evt) {
			if (this.getAttribute('class') == 'valid') {
				if(isSelected == false) {
					this.setAttribute('class', 'selectThis');
					inputSelect.value = this.getAttribute('id');
					showText(this.getAttribute('id'));
					isSelected = true;
				} else {
					document.getElementsByClassName('selectThis')[1].setAttribute('class', 'valid');
					this.setAttribute('class', 'selectThis');
					inputSelect.value = this.getAttribute('id');
					showText(this.getAttribute('id'));
				}
			} else if ((this.getAttribute('class') == 'selectThis')) {
				this.setAttribute('class', 'valid');
				hideText();
				inputSelect.value = '';
				isSelected = false;
			}

			function showText(seat){
				var location = seat.split('-');
				document.getElementById('row').innerText = location[0];
				document.getElementById('column').innerText = location[1];
				document.getElementById('showSelection').style.display = 'block';
				document.getElementById('submitButton').disabled = false;
				document.getElementById('alert').style.display = 'none';
			}

			function hideText(){
				document.getElementById('showSelection').style.display = 'none';
				document.getElementById('alert').innerText = '请选择您的座位';
				document.getElementById('alert').style.display = 'block';
				document.getElementById('submitButton').disabled = true;
			}
		}
	}
}

bind_click();

function showMsg(message){
	$('#showSelection').hide();
    $('#alert').text(message);
    $('#alert').show();
}
function response(data){
    $('#submitButton').prop('disabled', false);
    if ($('showSelection').css('display') == 'block')
    	$('showSelection').css('display', 'none');
    if (data.msg == 'invalidTicket') {
        showMsg('好像这张票是无效的><');
    } else {
        if (data.msg == 'invalidSeat'){
            showMsg('不好意思，座位已经被抢走啦～');
            for (var row = 0; row < data.seat.length; row++){
                for (var column = 0; column < data.seat[row].length; column++){
                    seat = (row+1) + '-' + (column+1)
                    if (data.seat[row][column] == 0){
                    	$('#'+seat).attr('class', 'empty');
                    } else if (data.seat[row][column] == 1) {
                    	$('#'+seat).attr('class', 'valid');
                    } else if (data.seat[row][column] == 2) {
                    	$('#'+seat).attr('class', 'selected');
                    }
                }
            }
            isSelected = false;
            bind_click();
        } else {
        	showMsg('恭喜，选座成功啦！');
            location.href = data.next_url;
        }
    }
}
$('#submitForm').on('submit', function(e) {
	e.preventDefault();

    $.ajax({
        url: window.location.pathname,
        type: "POST",
        data: {
            ticketID: $('#ticketID').val(),
            postSelect: $('#input').val()
        },
        dataType: "json",
        success: response,
        error: function() {
            showMsg('Unknown Error');
        }
    });
    return false;
});

var moveableDiv = document.getElementById('moveableDiv');
var dx, dy;

touch.on(moveableDiv, 'touchstart', function(ev){
    ev.preventDefault();
});

touch.on(moveableDiv, 'drag', function(ev){
    dx = dx || 0;
    dy = dy || 0;
    var offx = dx + ev.x + "px";
    var offy = dy + ev.y + "px";
    moveableDiv.style.webkitTransform = "translate3d(" + offx + "," + offy + ",0)";
});

touch.on(moveableDiv, 'dragend', function(ev){
    dx += ev.x;
    dy += ev.y;
});

var table = document.getElementById('selectSeat');

touch.on(table, 'touchstart', function(ev){
    ev.preventDefault();
}

var initialScale = 1;
var currentScale;

touch.on(table, 'pinch', function(ev){
    currentScale = ev.scale - 1;
    currentScale = initialScale + currentScale;
    currentScale = currentScale > 2 ? 2 : currentScale;
    currentScale = currentScale < 1 ? 1 : currentScale;
    table.style.webkitTransform = 'scale(' + currentScale + ')';
});

touch.on(table, 'pinchend', function(ev){
    initialScale = currentScale;
})