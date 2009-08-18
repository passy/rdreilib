function UpdateApplication() {
    bind_spinner();
    bind_check();

    function bind_spinner() {
        $(document).ajaxStart(function() {
            window.ua.update_image("/_shared/updater/images/spinner.apng");
        });
        $(document).ajaxStop(function() {
            window.ua.update_image();
        });
    }

    function bind_check() {
        $("#update_link").click(check_updates);
    }

    function check_updates() {
        // TODO: Show a spinner somewhere!
        $.getJSON("ajax/check_update", null,
        function(data) {
            if(data[0] > data[1]) {
                load_update_table(data[0]-data[1]);
            } else {
                $("#check1").hide();
                $("#check2").fadeIn();
            }
        });
        return false;
    }

    function load_update_table(count) {
        $("#content").load("ajax/update_skeleton").fadeIn();
        $("#update_count").text(count);
        $("#check1")
            .find("intro").hide().end()
            .find("available").fadeIn();
    }

}

UpdateApplication.prototype.update_image = function(img) {
    var $el = $("#featured img");
    var old = $el.attr('src');

    if(!img) {
        var img = $el.data('old_src');
    }

    $el.attr('src', img).data('old_src', old);
};
