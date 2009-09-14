/**
 * updater
 * ~~~~~~~~~~~
 * Main javascript file for the updater application.
 *
 * :copyright: date, Pascal Hartig <phartig@rdrei.net>
 * :license: GPL v3, see doc/LICENSE for more details.
 */

/*global $ */
/*jslint white: true, onevar: true, browser: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true */
"use strict";

function UpdateApplication() {

    function update_check(check_id, img) {
        $("#check")
            .find("div")
                .hide()
            .end().find(".check_" + check_id)
                .fadeIn();
        if (img) {
            window.ua.update_image(img);
        }
    }

    function on_ajax_error(data) {
        update_check(3, "/_shared/updater/images/error_box.png");
        if (data) {
            $("#error_data").text(data.error);
        }
    }

    function bind_spinner() {
        $(window.document).ajaxStart(function () {
            window.ua.update_image("/_shared/updater/images/spinner.apng");
        }).ajaxSuccess(function (event, xhr) {
            window.setTimeout(function () {
                // The wrapping here is not useless, because it prevents from
                // supplying timeout codes.
                window.ua.update_image();
            }, 100);
        }).ajaxError(on_ajax_error);
    }

    function load_update_table(count) {
        $("#content").load("ajax/update_skeleton").fadeIn();
        $("#update_count").text(count);
        update_check(1, "/_shared/updater/images/updates_available.png");
    }

    function check_updates() {
        $.getJSON("ajax/check_update", null,
        function (data) {
            if ('error' in data) {
                on_ajax_error(data);
            } else if (data[0] > data[1]) {
                load_update_table(data[0] - data[1]);
            } else {
                update_check(2, "/_shared/updater/images/up_to_date.png");
            }
        });
        return false;
    }

    function bind_check() {
        $("#update_link").click(check_updates);
    }

    bind_spinner();
    bind_check();
}

UpdateApplication.prototype.update_image = function (img, instant) {
    var $el, old;
    $el = $("#featured img");
    old = instant ? img : $el.attr('src');

    if (!img || instant) {
        img = $el.data('old_src');
    }

    $el.attr('src', img).data('old_src', old);
};
