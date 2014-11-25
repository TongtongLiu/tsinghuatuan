/**
 * Created by liutongtong on 11/26/14.
 */

function ajax_token() {
    $.post("",
    {
        openid: "{{ weixin_id }}",
    },
    function(data, status) {
        if (status == "success") {
            $("token-holder").val(data.token);
        } else {
            $("token-holder").val("Error token! Please refresh.");
        }
    });
}