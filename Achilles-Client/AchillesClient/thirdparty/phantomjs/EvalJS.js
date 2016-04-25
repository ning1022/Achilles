/*
 *  File:       EvalJS.js
 *  Author:     Himyth
 *
 *  利用phantomjs发起请求，得到返回的页面并且处理了JS
 *  Cookie、网络请求、POST/GET
 */

/*
 * 调用范例：
 * "./phantomjs" --disk-cache=true --load-images=false --web-security=false
 * --ignore-ssl-errors=true --ssl-protocol=any --output-encoding="UTF8"
 * "./EvalJS.js" "GET" "http://www.cc98.org" "NO_DATA" ".cc98.org" "cookie=1"
 */

var system = require("system");
var webpage = require("webpage");

if (system.args.length < 6) {
    console.log("Usage: phantomjs [options] evaljs_path " +
        "method target_url data cookie_domain cookies");
    phantom.exit();
}

var method = system.args[1];
var target_url = system.args[2];
var data = system.args[3];
var domain = system.args[4];
var cookies = system.args[5];
cookies = cookies.replace(/ /g, '').split(';');

// 发起请求
EvalJS(target_url, cookies, function() {
    return phantom.exit();
});

function EvalJS(target_url, cookies, callbackFinal) {
    var logged_ids = {};
    var type_forbidden = [
        'application/x-javascript',
        'text/css',
        'application/javascript'];

    var page = webpage.create();
    page.settings.userAgent =
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) ' +
        'AppleWebKit/537.36 (KHTML, like Gecko) ' +
        'Chrome/44.0.2403.89 Safari/537.36';

    // 添加cookie
    for (var i = 0; i < cookies.length; i++) {

        // 防止cookie中原本带了等号的情况
        var cookie = cookies[i].split(/=(.*)/);
        page.addCookie({
            'name'  : cookie[0],
            'value' : cookie[1],
            'domain': domain
        });
    }

    page.onResourceRequested = request_handler;
    page.onResourceReceived = first_response_handler;
    if (method == 'POST') {

        // 需要添加urlencoded头，大部分情况，不是也基本没有害处
        var post_setting = {
            operation: method,
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            data: data
        };
        return page.open(target_url, post_setting, callback_req);
    }
    else if (method == 'GET') {
        return page.open(target_url, callback_req);
    }
    else {
        return callbackFinal();
    }

    // 回调函数，输出页面内容
    function callback_req(status) {
        if (status === "success") {
            console.log(page.content);
        }
        return callbackFinal();
    }

    // 请求包的hook
    function request_handler(requestData, networkRequest) {
        if (requestData.method == 'POST') {

            // 主要是AJAX请求的POST包
            var html = '<FORM METHOD="POST" ACTION="' + requestData.url +
                '">FROM_REQUEST';
            var datas = requestData.postData.split('&');
            for (var i = 0; i < datas.length; i++) {
                var item = datas[i].split(/=(.*)/);
                html += '<INPUT NAME="' + item[0] +
                    '" VALUE="' + item[1] + '"></INPUT>';
            }
            html += '</FORM>';
            console.log(html);

            logged_ids[requestData.id] = 1;
        }
    }

    // 接收包的hook，只记录第一个返回包的状态码
    function first_response_handler(response) {
        logged_ids[response.id] = 1;

        // 只调用一次，随后转而调用response_handler
        page.onResourceReceived = response_handler;

        // 记录状态码
        console.log('<STAT CODE="' + response.status + '">FROM_RESPONSE</STAT>');

        // 跳转情况下，记录跳转URL，放弃本次请求
        if (response.status == 302 || response.status == 301) {
            console.log('<A HREF="' + response.redirectURL + '">FROM_RESPONSE</A>');
            return callbackFinal();
        }
    }

    // 接收包的hook，图片请求已经在命令行中禁用，所以这里还需要过滤
    function response_handler(response) {
        // POST请求已经在request的时候处理过了
        if (response.id in logged_ids) {
            return;
        }

        // script和css的请求，这些请求会正常执行，但是不会被记录到A标签中
        if (in_array(type_forbidden, response.contentType)) {
            return;
        }

        // 记录请求URL
        console.log('<A HREF="' + response.url + '">FROM_RESPONSE</A>');
    }
}

// debug
function show_debug(obj) {
    console.log(JSON.stringify(obj));
}

function in_array(arr, str) {
  for (var i = 0; i < arr.length; i++) {
    if (str == arr[i])
        return true;
  }
  return false;
}
