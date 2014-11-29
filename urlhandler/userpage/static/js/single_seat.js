var isSelected = false;

document.getElementById('showNumToSelect').style.display = "none";
document.getElementById('showSelection').style.display = "none";

function bind_tap(){
    var valid_list = document.getElementsByClassName('valid');
    var inputSelect = document.getElementById('input');
    for (var i = 0; i < valid_list.length; i++) {
        touch.on(valid_list[i], 'tap', function (evt) {
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
            } else {
                return;
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
        });
    }
}

bind_tap();

