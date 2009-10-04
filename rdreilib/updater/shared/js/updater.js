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

function UpdateListApplication() {
    function _start_verify() {
        var id = $(this).attr('id').split('verify_')[1];
        $.getJSON("ajax/verify/"+id, null, this.on_verified);
        return false;
    }
    $(".action.verify").click(_start_verify);
}

UpdateListApplication.prototype.on_verified = function (data) {
    console.log("Verification state: ", data);
};

function UpdateTableApplication() {
    // Not actually a html table, but it contains data in kind of a grid.
    this.$table = $("#posts-list");
    this.$table.find(".action.download").one('click', this.download_start);
    this.downloads = {};
}

UpdateTableApplication.prototype.download_start = function () {
    // TODO: CSRF
    var $this, download_id;
    $this = $(this);
    download_id = $this.attr('id').split('start_download_')[1];
    $.post("ajax/download/start", {
        revision: download_id
    }, window.uta.on_download_ended, 'json');
    // Replace the download button with a status bar.
    $this.click(window.uta.download_stop).text("Cancel").after(
        $("<div>").hide().attr('id', 'download_progressbar_' + download_id).progressbar({
            value: 0
        }).effect('drop', {mode: 'show'})
    );
    // TODO: Disable other downloads or allow them in the downloads controller
    // as well and only make upgrades exclusive. I think this is not really
    // useful. It would be better to make installing previous updates necessary
    // in order to install later ones.

    // Time to settle request.
    window.setTimeout(function () {
        window.uta.request_download_update(download_id);
    }, 1000);
};

UpdateTableApplication.prototype.request_download_update = function (download_id) {
    $.getJSON("ajax/download/status/" + download_id, function (data) {
        window.uta.update_download_step(download_id, data);
    });
};

UpdateTableApplication.prototype.update_download_step = function (download_id, data) {
    if ('error' in data) {
        return window.updater.on_ajax_error(data);
    }
    var progress, $bar;
    progress = data.progress;
    $bar = $("#download_progressbar_" + download_id);
    $bar.progressbar('value', progress);

    if (progress === 100) {
        // Update stuff.
    } else {
        // Continue updating the old school way until we enable comet. (:
        // 500ms seems low, but this is supposed to be local and we
        // create db entries every downloaded block, so why not?
        window.setTimeout(function () {
            window.uta.request_download_update(download_id);
        }, 500);
    }
};

UpdateTableApplication.prototype.download_stop = function () {
    console.error("Not implemented, yet.");
};

UpdateTableApplication.prototype.on_download_ended = function (data) {
    if ('error' in data) {
        return window.updater.on_ajax_error(data);
    }
    console.log("Coming soon.");
};

function UpdateApplication(arg) {

    function update_check(check_id, img) {
        return window.updater.update_check(check_id, img);
    }

    function on_ajax_error(data) {
        return window.updater.on_ajax_error(data);
    }

    function bind_spinner() {
        $(window.document).ajaxStart(function () {
            window.updater.update_image("/_shared/updater/images/spinner.apng");
        }).ajaxSuccess(function (event, xhr) {
            window.updater.update_image();
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

    if (arg === "list") {
        this.list_app = new UpdateListApplication();
    }
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

UpdateApplication.prototype.on_ajax_error = function (data) {
    window.updater.update_check(3, "/_shared/updater/images/error_box.png");
    if (data) {
        $("#error_data").text(data.error);
    }
};

UpdateApplication.prototype.update_check = function (check_id, img) {
    $("#check")
        .find("div")
            .hide()
        .end().find(".check_" + check_id)
            .fadeIn();
    if (img) {
        window.updater.update_image(img);
    }
};
