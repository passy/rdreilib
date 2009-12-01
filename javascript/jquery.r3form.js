/**
 * rdreilib/jquery.form.js
 * ~~~~~~~~~~~~~~~~~~~~~~~
 * 
 * Form helpers that integrate nicely into jquery.
 *
 * :copyright: date, Pascal Hartig <phartig@rdrei.net>
 * :license: BSD, see doc/LICENSE for more details.
 */

/*global jQuery, window, R3 */
/*jslint white: true, onevar: true, browser: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true */
"use strict";

(function ($) {
    /**
     * This provides some wild, black magic that will not satisfy everyone.
     *
     * This works really great in conjunction with __``http://jquery.malsup.com/form/jquery.form.js``.
     *
     * @param data: Data dictionary parsed from json.
     * @param options['evil']: Eval data.success.cmd commands if available.
     * @param options['errors']: Enable automagic error display.
     * @param options['form_errors']: Key that holds validation errors in ``data``.
     * @param options['error_list_class']: CSS class for <ul> element holding
     * @param options['error_callback']: If data has an error attribute containing
     * a string, it's passed to this function.
     * the form errors.
     *
     */
    $.fn.r3_parseFormData = function (data, options) {
        var settings = {
            evil: false,
            errors: false,
            error_key: 'form_errors',
            error_list_class: 'errorlist',
            error_callback: window.alert
        }, $this = $(this),
           is_error = false;

        $.extend(settings, options);

        if (typeof(data) !== 'object') {
            throw new Error("Data is not a valid object.");
        }

        function handle_form_errors() {
            /// Creates a unordered list element containing the form errors.

            function attach_global($error_list) {
                // Attach the error list to the global selector.
                $error_list.addClass("global");
                $this.find("> *:first").before($error_list);
            }

            if (settings.error_key in data) {
                is_error = true;
                $.each(data[settings.error_key], function (key, value) {
                    var $error_list = $($.format(
                        '<ul class="{0}" />',
                        settings.error_list_class)
                    ).hide(), $element;

                    // There can be multiple errors on each item.
                    $.each(value, function () {
                        // Append the actual error message
                        $error_list.append($.format("<li>{0}</li>", this));
                    });

                    // Figure out where to attach.
                    if (key === '__all__') {
                        // It's a global error.
                        attach_global($error_list);
                    } else {
                        // Try to find the element.

                        // Name first:
                        $element = $this.find($.format("[name='{0}']", key));
                        if ($element.length === 0) {
                            // Find by #id_
                            $element = $this.find("#id_" + key);
                        }
                        if ($element.length === 0) {
                            // Find by containing name
                            $element = $this.find($.format("[name*='{0}']", key));
                        }
                        if ($element.length === 0) {
                            // Attach globally and send a warning.
                            R3.log.warn("Could not find element %o. Attaching error message to global.", key);
                            attach_global($error_list);
                        } else {
                            $element.parent().before($error_list);
                        }
                    }

                });

            }
        }

        function handle_result() {
            // Trigger events based on success or failure.
            if ($.isFunction(settings.error_callback) && 'error' in data) {
                is_error = true;
                settings.error_callback(data.error);                    
            } else if ('success' in data) {
                // 'Success' superseeded form errors.
                is_error = false;
                if (settings.evil && 'cmd' in data.success) {
                    eval(data.success.cmd);
                }
                R3.log.debug("R3ParseForm successful!", data);
                $this.trigger('r3-form-success', data.success);
            }

            if (is_error) {
                R3.log.info("Caught some form errors in %o.", data);
                $this.trigger('r3-form-error', data);
            }
        }
        
        if (settings.errors) {
            handle_form_errors();
        }

        handle_result();

        // We don't need each here, imho.
        return this;
        
    };

    if($.R3 === undefined) {
        $.R3 = {};
    }

    $.R3.TokenStore = function (options) {
        var that = {},
            settings = {
                'cookie_name': 'r3csrfprot'
            };

        $.extend(settings, options);

        that.get = function () {
            // Returns the current CSRF secret
            return $.cookie(settings.cookie_name);
        };

        that.get_dict = function () {
            // Returns the current CSRF secret in a dict with 'csrf_token' as key.
            return {'_csrf_token': that.get()};
        };

        return that;
    };

    // Override this with your own to set custom options.
    $.R3.tokenstore = TokenStore();
}(jQuery));
