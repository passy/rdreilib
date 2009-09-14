/**
 * updater
 * ~~~~~~~
 * Main javascript file for the updater application.
 *
 * :copyright: date, Pascal Hartig <phartig@rdrei.net>
 * :license: GPL v3, see doc/LICENSE for more details.
 */

/*global $, window */
/*jslint white: true, onevar: true, browser: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
"use strict";

function UpdateTableApplication() {
    // Not actually a html table, but it contains data in kind of a grid.
    this.$table = $("#posts-list");
    this.$table.find(".action.download").one('click', this.download_start);
}

UpdateTableApplication.prototype.download_start = function () {
    // TODO: CSRF
    var $this = $(this);
    var download_id = $this.attr('id').split('start_download_')[1];
    $.post("ajax/download/start", {
        revision: download_id
    }, window.uta.on_download_started, 'json');
    // Replace the download button with a status bar.
    $this.click(window.uta.download_stop).text("Cancel").after(
        $("<div>").hide().attr('id', 'download_progressbar_'+download_id).progressbar({
            value: 50
        }).effect('drop', {mode: 'show'})
    );
    // TODO: Disable other downloads or allow them in the downloads controller
    // as well and only make upgrades exclusive. I think this is not really
    // useful. It would be better to make installing previous updates necessary
    // in order to install later ones.
};

UpdateTableApplication.prototype.update_download_step = function (download_id, progress) {
    $("#download_progressbar_"+download_id).animate({width: progress+"%"});
};

UpdateTableApplication.prototype.download_stop = function () {
    console.error("Not implemented, yet.");
};

UpdateTableApplication.prototype.on_download_started = function () {
    console.log("Coming soon.");
};

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
            window.ua.update_image();
        }).ajaxError(on_ajax_error);
    }

    function on_table_load() {
        window.uta = new UpdateTableApplication();
    }

    function load_update_table(count) {
        $("#content").load("ajax/update_skeleton", on_table_load).fadeIn();
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
