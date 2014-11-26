/**
 * Created by liutongtong on 11/26/14.
 */

var xmlhttp = null;

function hideElem(id) {
    document.getElementById(id).setAttribute('style', 'display:none');
}

function showElem(id) {
    document.getElementById(id).setAttribute('style', 'display:block');
}

function clearHelp(groupid, helpid) {
    document.getElementById(groupid).setAttribute('class', 'input-group');
    //document.getElementById(helpid).setAttribute('hidden', 'hidden');
    //document.getElementById(helpid).setAttribute('style', 'display:none;');
    hideElem(helpid);
}

function clearAllHelps() {
    clearHelp('activityGroup', 'helpActivity');
    clearHelp('tokenGroup', 'helpToken');
    clearHelp('submitGroup', 'helpSubmit');
}

function showSuccess(groupid, helpid) {
    document.getElementById(groupid).setAttribute('class', 'input-group has-success');
    //document.getElementById(helpid).setAttribute('hidden', 'hidden');
    //hideElem(helpid);
}

function showError(groupid, helpid, text) {
    var dom = document.getElementById(helpid);
    dom.innerText = text;
    //dom.removeAttribute('hidden');
    //showElem(helpid);
    document.getElementById(groupid).setAttribute('class', 'input-group has-error');
}

function disableOne(id, flag) {
    var dom = document.getElementById(id);
    if (flag) {
        dom.setAttribute('disabled', 'disabled');
    } else {
        dom.removeAttribute('disabled');
    }
}

function disableAll(flag) {
    disableOne('selectActivity', flag);
    disableOne('inputToken', flag);
    disableOne('submitBtn', flag);
}

function showLoading(flag) {
    //var dom = document.getElementById('helpLoading');
    if (flag) {
        //dom.removeAttribute('hidden');
        showElem('helpLoading');
    } else {
        //dom.setAttribute('hidden', 'hidden');
        hideElem('helpLoading');
    }
}

function uc_readyStateChanged() {
    if (xmlhttp.readyState==4)
    {// 4 = "loaded"
        if (xmlhttp.status==200)
        {// 200 = OK
            var result = xmlhttp.responseText;
            switch (result)
            {
                case 'Accepted':
                    //document.getElementById('validationHolder').setAttribute('hidden', 'hidden');
                    hideElem('validationHolder');
                    //document.getElementById('successHolder').removeAttribute('hidden');
                    showElem('successHolder');
                    return;

                case 'Rejected':
                    showError('submitGroup', 'helpSubmit', '学号或密码错误！请输入学号和info登录密码');
                    break;

                case 'Timeout':
                    showError('submitGroup', 'helpSubmit', '连接超时！请稍后重试');
                    break;

                case 'Error':
                    showError('submitGroup', 'helpSubmit', '出现了奇怪的错误，我们已经记录下来了，请稍后重试。')
                    break;

                default:
                    window.location.href = result;
            }
        }
        else
        {
            showError('submitGroup', 'helpSubmit', '服务器连接异常，请稍后重试。')
        }
        showLoading(false);
        disableAll(false);
    }
}

function uc_bind2ticket(openid) {
    if (checkActivity() & checkToken()) {
        disableAll(true);
        showLoading(true);

        var form = document.getElementById('bindForm'),
            elems = form.elements,
            url = form.action,
            params = "openid=" + encodeURIComponent(openid),
            i, len;
        setMaxDigits(150);
        for (i = 0, len = elems.length; i < len; ++i) {
            params += '&' + elems[i].name + '=' + encodeURIComponent(elems[i].value);
        }

        xmlhttp = new XMLHttpRequest();
        xmlhttp.open('POST', url, true);
        xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xmlhttp.onreadystatechange = uc_readyStateChanged;
        xmlhttp.send(params);
        document.getElementById('inputToken').value = '';
    }
    return false;
}

function checkNotEmpty(groupid, helpid, inputid, hintName) {
    if (document.getElementById(inputid).value.trim().length == 0) {
        document.getElementById(groupid).setAttribute('class', 'input-group has-error');
        //var dom = document.getElementById(helpid);
        //dom.innerText = '请输入' + hintName + '！';
        //dom.removeAttribute('hidden');
        //showElem(helpid);
        return false;
    } else {
        showSuccess(groupid, helpid);
        return true;
    }
}

function checkActivity() {
    return checkNotEmpty('activityGroup', 'helpActivity', 'selectActivity', '选择活动');
}

function checkToken() {
    return checkNotEmpty('tokenGroup', 'helpToken', 'inputPassword', '对方令牌');
}

window.setupWeixin({'optionMenu':false, 'toolbar':false});

clearAllHelps();

/*
document.getElementById('inputUsername').onfocus = function(){
    setfooter();
}

document.getElementById('inputPassword').onfocus = function(){
    setfooter();
}*/

