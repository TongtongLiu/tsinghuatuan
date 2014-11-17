{% extends "mobile_base.html" %}

{% load staticfiles %}

{% block title %}
绑定学号 - 清华紫荆之声
{% endblock %}

{% block css %}
<link href="{% static "css/validation.css" %}?_=3" rel="stylesheet" type="text/css" />
{% endblock %}

{% block js %}
    <script src="{% static "lib/RSA/BigInt.js" %}"></script>
    <script src="{% static "lib/RSA/Barrett.js" %}"></script>
    <script src="{% static "lib/RSA/RSA.js" %}"></script>
    <script src="{% static "js/validation_student.js" %}?_=1"></script>
    <script>
    function ajaxForm() {
        submitValidation('{{ openid }}');
    }
    window.addEventListener('load', function() {showValidation({{ isValidated }});}, false);
    </script>
{% endblock %}

{% block header %}
<img class="header-img" src="{% static "img/logo.png" %}" />
{% endblock %}

{% block theme %}
    用户认证
{% endblock %}

{% block content %}
    <div id="validationHolder">
        <form class="form-horizontal" role="form" action="{% url "userpage.views.validate_post" %}" method="post" id="validationForm" onsubmit="return false;">
            {% csrf_token %}
          <div class="form-group" id="usernameGroup">
            <label for="inputUsername" class="col-xs-3 control-label">学号</label>
            <div class="col-xs-9">
              <input type="tel" class="form-control" id="inputUsername" placeholder="请输入您的学号" name="username" value="{{ studentid }}" onblur="checkUsername();">
              <span class="help-block" id="helpUsername"></span>
            </div>
          </div>
          <div class="form-group" id="passwordGroup">
            <label for="inputPassword" class="col-xs-3 control-label">密码</label>
            <div class="col-xs-9">
              <input type="password" class="form-control" id="inputPassword" placeholder="使用info密码进行登录" name="password" onblur="checkPassword();">
              <span class="help-block" id="helpPassword"></span>
            </div>
          </div>
          <div class="form-group" id="submitGroup">
            <div class="col-xs-offset-3 col-xs-9">
              <button onclick="ajaxForm();" class="btn btn-default" id="submitBtn">认证</button>
              <p class="help-block" id="helpLoading" style="display: none"><img src="{% static "img/loading.gif" %}">正在认证，请稍候...</p>
              <p class="help-block" id="helpSubmit"></p>
            </div>
          </div>
        </form>
    </div>
    <div id="successHolder" style="display: none">
        <img src="{% static "img/success.png" %}" />
        <p>认证成功！</p>
        <p>您已经可以使用“紫荆之声”的全部功能了！</p>
    </div>
{% endblock %}
