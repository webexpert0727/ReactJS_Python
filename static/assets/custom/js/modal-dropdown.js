/* Modal dropdown -> change selected item on click */
$(".modal-hc .dropdown-menu li a").click(function(e) {
  e.preventDefault();

  var src = $(this).find("img").attr("src");
  var name = $(this).find("div p:nth-child(1)").text();
  // var sub = $(this).find("div p:nth-child(2)").text();

  var $img = "<img src='" + src + "' />";
  var $name = "<p>" + name + "</p>";
  // var $sub = "<p class='s-h1'><small>" + sub + "</small></p>";
  // var $dropdownItem = $img + "<div>" + $name + $sub + "</div>";
  var $dropdownItem = $img + "<div>" + $name + "</div>";

  $(this).parents(".dropdown").find('.btn .dropdown-item').html($dropdownItem);
  $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
  if ($(this).attr("brew")) {
    $(this).parents(".dropdown").find('.btn')
      .attr("data-brew-id", $(this).attr("data-id"));
  }
  else {
    $(this).parents(".dropdown").find('.btn')
      .attr("data-package-id", $(this).attr("data-package"));
  }

  $(this).parents(".dropdown").removeClass("open");
  $(this).parents(".dropdown-menu").css("display", "none");

});
