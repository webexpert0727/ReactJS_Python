/* ---------------------------------------------- /*
 * Transparent navbar animation
/* ---------------------------------------------- */

window.onload = function () {
  var SM_DEVICE_SIZE = 768
  var navbar = $('.navbar-custom')

  var scrWidth = $(window).width()
  var topScroll = $(window).scrollTop()

  navbar.addClass('navbar-transparent')

  $(window).scroll(function () {
    topScroll = $(window).scrollTop()
    scrWidth = $(window).width()

    if (topScroll >= 5) {
      navbar.switchClass('navbar-transparent', 'navbar-white')
    } else {
      navbar.switchClass('navbar-white', 'navbar-transparent')
    }
  }).scroll()
}

$('.navbar-toggle').click(function (event) {
  var navbar = $('#navbar')
  var topScroll = $(window).scrollTop()

  if (topScroll <= 5) {
    if (!$('#custom-collapse').hasClass('collapse in')) {
      navbar.switchClass('navbar-transparent', 'navbar-white')
    } else {
      navbar.switchClass('navbar-white', 'navbar-transparent')
    }
  }
})
