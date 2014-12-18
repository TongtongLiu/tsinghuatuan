var numToSelect = 2;

document.getElementById('showSelection').style.display = 'none';
document.getElementById('alert').style.display = 'none';


function bind_tap(){
    var valid_list = document.getElementsByClassName('valid');
    var inputSelect = document.getElementById('input');
    for (var i = 1; i < valid_list.length; i++) {
        touch.on(valid_list[i], 'tap', function (evt) {
            if (this.getAttribute('class') == 'valid') {
                if(numToSelect > 0) {
                    this.setAttribute('class', 'selectThis');
                    inputSelect.value += '-' + this.getAttribute('id') + ',';
                    numToSelect--;
                    showText();
                } else {
                }
            } else if ((this.getAttribute('class') == 'selectThis')) {
                this.setAttribute('class', 'valid');
                inputSelect.value.replace('-' + this.getAttribute('id') + ',', '');
                numToSelect++;
                showText();
            } else {
                return;
            }
            function showText(seat){
                document.getElementById('num').innerText = numToSelect;
                document.getElementById('showNumToSelect').style.display = 'block';
                document.getElementById('alert').style.display = 'none';
                if (numToSelect == 0)
                    document.getElementById('submitButton').disabled = false;
            }
        });
    }
}

bind_tap();

