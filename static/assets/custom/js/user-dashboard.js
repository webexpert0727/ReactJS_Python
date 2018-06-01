// Bags subscription click events
$('.js-open-prefs').click(function (e) {
  var $sub = $(this).closest('.js-curr-subscription');
  $sub.find('.js-pref-content').addClass('hide');
  $sub.find('.js-pref-prefs').removeClass('hide');
});

$('.js-close-prefs').click(function (e) {
  var $sub = $(this).closest('.js-curr-subscription');
  $sub.find('.js-pref-content').removeClass('hide');
  $sub.find('.js-pref-prefs').addClass('hide');
});

// Open tab from sidemenu using data-tab attribute of clicked element
$('.tab-select').click(function (event) {
  event.preventDefault();
  var tabToOpen = $(this).data('tab');

  $('#tab-' + tabToOpen).tab('show');
})

// Solution code snippet for opening multiple modals with Bootstrap
// from: http://stackoverflow.com/questions/19305821/multiple-modals-overlay
$(document).ready(function () {
  $(document).on('show.bs.modal', '.modal', function () {
    var zIndex = 9999 + (10 * $('.modal:visible').length);
    $(this).css('z-index', zIndex);
    setTimeout(function() {
      $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
    }, 0);
  });

  $(document).on('hidden.bs.modal', '.modal', function () {
    $('.modal:visible').length && $(document.body).addClass('modal-open');
  });
})

$(function() {
  $('#panel2').on('show.bs.collapse', function () {
    $("#panel1").slideToggle();
  })
})
$(function() {
  $('#panel2').on('hide.bs.collapse', function () {
    $("#panel1").slideToggle();
  })
})

$(".dropdown-item").click(function() {
  $(this).closest(".dropdown-menu").hide();
});
