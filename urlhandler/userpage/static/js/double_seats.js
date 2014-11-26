var numToSelect = 2;

function bind_tap(){
    var valid_list = document.getElementsByClassName('valid');
    var inputSelect = document.getElementById('input');
    for (var i = 0; i < valid_list.length; i++) {
        touch.on(valid_list[i], 'tap', function (evt) {
            if (this.getAttribute('class') == 'valid') {
                if(numToSelect > 0) {
                    this.setAttribute('class', 'selectThis');
                    inputSelect.value += this.getAttribute('id') + ',';
                    numToSelect--;
                    showText();
                } else {
                    alert("you can choose only two seats");
                }
            } else if ((this.getAttribute('class') == 'selectThis')) {
                this.setAttribute('class', 'valid');
                inputSelect.value.replace(this.getAttribute('id') + ',', '');
                numToSelect++;
                showText();
            }
            function showText(seat){
                document.getElementById('num').innerText = numToSelect;
                document.getElementById('showSelection').style.display = 'block';
                document.getElementById('alert').style.display = 'none';
                if (numToSelect == 0)
                    document.getElementById('submitButton').disabled = false;
            }
        });
    }
}

bind_tap();

