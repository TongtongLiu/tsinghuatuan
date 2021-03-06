function showMsg(message){
    $('#showSelection').hide();
    $('#showNumToSelect').hide();
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
        } else {
            showMsg('恭喜，选座成功啦！');
            location.href = data.next_url;
        }
    }
}
$('#submit_btn').on('click', function(e) {
    e.preventDefault();
    /*
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
    */

    var options = {
        dataType: 'json',
        beforeSubmit: beforeSubmit,
        success: response,
        error: function(XMLHttpRequest, textStatus, errorThrown) {
                        alert(XMLHttpRequest.status);
                        alert(XMLHttpRequest.readyState);
                        alert(textStatus);
                    },
    }
    $('#submitForm').ajaxSubmit(options);
    return false;
});

function submitResponse(data) {
    alert('submitResponse');
}

function submitError(data) {
    alert('submitError');
}

function submitComplete(data) {
    alert('submitComplete');
}

function beforeSubmit(data) { 

}


var moveableDiv = document.getElementById('moveableDiv');
var dx, dy;

touch.on(moveableDiv, 'touchstart', function(ev){
	ev.preventDefault();
});

touch.on(moveableDiv, 'drag', function(ev){
    dx = dx || 0;
    dy = dy || 0;
    var offx, offy;
    if (dx + ev.x < (1-initialScale)*$('#selectSeat').width()/2) {
        offx = dx + (ev.x * 0.3) + "px";
    } else if (dx + ev.x > (initialScale-1) * $('#selectSeat').width() / 2) {
        offx = dx + (ev.x * 0.3) + "px";
    } else {
        offx = dx + ev.x + "px";
    }
    if (dy + ev.y < (1-initialScale)*$('#selectSeat').height()/2) {
        offy = dy + (ev.y * 0.3) + "px";
    } else if (dy + ev.y > (initialScale-1)*$('#selectSeat').height()/2) {
        offy = dy + (ev.y * 0.3) + "px";
    } else {
        offy = dy + ev.y + "px";
    }
    moveableDiv.style.webkitTransform = "translate3d(" + offx + "," + offy + ",0)";
});

touch.on(moveableDiv, 'dragend', function(ev){
    if (dx + ev.x < (1-initialScale)*$('#selectSeat').width()/2) {
        dx = (1-initialScale)*$('#selectSeat').width()/2;
    } else if (dx + ev.x > (initialScale-1) * $('#selectSeat').width() / 2) {
        dx = (initialScale-1) * $('#selectSeat').width()/2;
    } else {
        dx += ev.x
    }
    if (dy + ev.y < (1-initialScale)*$('#selectSeat').height()/2) {
        dy = (1-initialScale)*$('#selectSeat').height()/2;
    } else if (dy + ev.y > (initialScale-1)*$('#selectSeat').height()/2) {
        dy = (initialScale-1)*$('#selectSeat').height()/2;
    } else {
        dy += ev.y;
    }
    moveableDiv.style.webkitTransition = "all 0.4s ease 0s";
    moveableDiv.style.webkitTransform = "translate3d(" + dx + "px, " + dy + "px,0)";
    setTimeout("moveableDiv.style.webkitTransition = ''",400);
});

var table = document.getElementById('selectSeat');


touch.on(table, 'touchstart', function(ev){
	ev.preventDefault();
});

var initialScale = 1;
var currentScale;

touch.on(table, 'pinch', function(ev){
    currentScale = ev.scale - 1;
    currentScale = initialScale + currentScale;
    currentScale = currentScale > 6 ? 6 : currentScale;
    currentScale = currentScale < 1 ? 1 : currentScale;
    table.style.webkitTransform = 'scale(' + currentScale + ')';
});

touch.on(table, 'pinchend', function(ev){
    initialScale = currentScale;
    if (dx < (1-initialScale)*$('#selectSeat').width()/2) {
        dx = (1-initialScale)*$('#selectSeat').width()/2;
    } else if (dx > (initialScale-1) * $('#selectSeat').width() / 2) {
        dx = (initialScale-1) * $('#selectSeat').width()/2;
    } else {
        dx = dx; 
    }
    if (dy < (1-initialScale)*$('#selectSeat').height()/2) {
        dy = (1-initialScale)*$('#selectSeat').height()/2;
    } else if (dy > (initialScale-1)*$('#selectSeat').height()/2) {
        dy = (initialScale-1)*$('#selectSeat').height()/2;
    } else {
        dy = dy ;
    }
    moveableDiv.style.webkitTransition = "all 0.4s ease 0s";
    moveableDiv.style.webkitTransform = "translate3d(" + dx + "px, " + dy + "px,0)";
    setTimeout("moveableDiv.style.webkitTransition = ''",400);
});

function setHeightAndWidth() {
    var tableWidth = $('#tableContainer').width() * 0.8;
    var tableHeight = $('#tableContainer').height() * 0.8;
    var rows = $('#selectSeat').children('tbody').children('tr').length;
    var columns = $('#selectSeat').children('tbody').children('tr').children('td').length / rows;
    cellHeight = tableHeight / rows;
    cellWidth = tableWidth / columns;
    len = cellHeight > cellWidth ? cellHeight : cellWidth;
    border = len * 0.15;
    $('#selectSeat')[0].style.borderSpacing = border + "px";
    len = len * 0.85;
    $('#selectSeat').children('tbody').children('tr').children('td').height(len);
    $('#selectSeat').children('tbody').children('tr').children('td').width(len);
    var windowHeight = $(document).height();
    var divHeight = $('#moveableDiv').height();
    $('#tableContainer').height(windowHeight * 0.6);
    $('#moveableDiv').css('top', (windowHeight*0.6 - divHeight) / 2  + 'px')
}
setHeightAndWidth();
