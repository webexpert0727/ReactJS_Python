$("#local-site").on("click", function(){
    $("input[name='is_global']").val("");
//     console.log("Go to Local");
//     $.ajax({
//         url: "choose-country/",
//         method: "POST",
//         headers: {'X-CSRFToken': getCookie('csrftoken')},
//         data: {
//             global: $(this).attr("id") == "global-site"
//         },
//         success: function(data) {
//             console.log("Success:", data);
//         }
//     });
});

$("#global-site").on("click", function(e){
    e.preventDefault();

    $("input[name='is_global']").val(true);

    var width = $(this).width();
    $("#welcome-country").width(width);
    $(this).addClass("hide");


    $("#welcome-country").removeClass("hide");
    // var event = document.createEvent('MouseEvents');
    // event.initMouseEvent('mousedown', true, true, window);
    // $("#welcome-country").dispatchEvent(event);

    // $('#welcome-country option:contains("Afghanistan")').prop('selected', true);
    // $(".country-select-flag").attr("src", '/static/flags/my.gif');

    // $("#welcome-country").click();

//     console.log("Go to Global");
//     $.ajax({
//         url: "choose-country/",
//         method: "POST",
//         headers: {'X-CSRFToken': getCookie('csrftoken')},
//         data: {
//             global: $(this).attr("id") == "global-site"
//         },
//         success: function(data) {
//             console.log("Success:", data);
//         }
//     });
});

$("#welcome-country").on("change", function(){
    console.log("changed");

    if ($(this).val() == "SG") {
        console.log("Not global, Singapore.");
        $("input[name='is_global']").val("");
    };
   $(this).parent('form').submit();
});
