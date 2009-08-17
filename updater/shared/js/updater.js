function UpdateApplication() {
    bind_check();

    function bind_check() {
        $("#update_link").click(check_updates);
    }

    function check_updates() {
        // TODO: Show a spinner somewhere!
        $.getJSON("ajax/check_update", null,
        function(data) {
            if(data[0] > data[1]) {
                load_update_table();
            } else {
                $("#check1").hide();
                $("#check2").fadeIn();
            }
        });
        return false;
    }

    function load_update_table() {
        $("#content").load("ajax/update_skeleton").fadeIn();
    }

}
