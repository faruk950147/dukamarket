!function (s) {
    "use strict";

    // Light/Dark switch
    s(".switch").on("click", function () {
        s("body").toggleClass("light");
        s(".switch").toggleClass("switched");
    });

    // Back to top progress
    s(document).ready(function () {
        var e = document.querySelector(".progress-wrap path");

        if (e) { // Check if element exists
            var t = e.getTotalLength();
            e.style.transition = e.style.WebkitTransition = "none";
            e.style.strokeDasharray = t + " " + t;
            e.style.strokeDashoffset = t;
            e.getBoundingClientRect();
            e.style.transition = e.style.WebkitTransition = "stroke-dashoffset 10ms linear";

            var o = function () {
                var o = s(window).scrollTop(),
                    r = s(document).height() - s(window).height(),
                    i = t - o * t / r;
                e.style.strokeDashoffset = i;
            };

            o();
            s(window).scroll(o);

            jQuery(window).on("scroll", function () {
                jQuery(this).scrollTop() > 50
                    ? jQuery(".progress-wrap").addClass("active-progress")
                    : jQuery(".progress-wrap").removeClass("active-progress")
            });

            jQuery(".progress-wrap").on("click", function (s) {
                s.preventDefault();
                jQuery("html, body").animate({ scrollTop: 0 }, 550);
                return false;
            });
        }
    })
}(jQuery);