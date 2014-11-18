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
    if($('showSelection').css('display') == 'block')
    	$('showSelection').css('display', 'none');
    if (data.msg == 'invalidTicket') {
        showMsg('好像这张票是无效的><');
    }else{
    	if(data.msg == 'invalidSeat'){
        	showMsg('不好意思，座位已经被抢走啦～');
        } else {
        	showMsg('恭喜，选座成功啦！');
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


    var data = {
    	type: 'post',
        dataType: 'json',
        beforeSubmit: function(){return true},
        success: response
    }
    $('#submitButton').prop('disabled', true);

    $(this).ajaxSubmit(data);
    return false;
});
