var lastWindowWidth = $(window).width();
var package_mapper = {
      "GR": 'Ground (200g)',
      "WB": 'Wholebeans (200g)',
      "DR": 'Drip bags (x10)',
      "PODS": 'ShotPods (x 20)',
      "BO": "6x330ml bottles pack",
    }
var package_mapper_discovery = {
      "GR": 'Ground (3 x 80g)',
      "WB": 'Wholebeans (3 x 80g)',
      "DR": 'Drip bags (3 x 4)'
}

$(document).ready(function() {

  if (localStorage.getItem("cart") &&  localStorage.getItem("cart") !== "[]") {
    $("#btn-checkout-cart").attr('disabled', false);

    cart_list = JSON.parse(localStorage.getItem("cart"));

    $.each(cart_list, function(i, cart_item) {
      $("#menu-cart")
      .prepend(
        $("<li>").attr("id", "cart-" + cart_item.coffee_id + cart_item.brew_method + cart_item.package_method)
        .append(
          $("<div>")
          .append(
            $("<a>").append(cart_item.coffee_name)
            .append(
              $("<block>")
              .append(
                $("<input>").attr("name", "coffee_id").attr("value", cart_item.coffee_id)
                .attr("type", "hidden"))
              .append(
                $("<input>").attr("name", "coffee_name").attr("value", cart_item.coffee_name)
                .attr("type", "hidden"))
              .append(
                $("<input>").attr("name", "brew_method").attr("value", cart_item.brew_method)
                .attr("type", "hidden"))
              .append(
                $("<input>").attr("name", "package_method").attr("value", cart_item.package_method)
                .attr("type", "hidden"))
              .append(
                $("<input>").attr("name", "price").attr("value", cart_item.price)
                .attr("type", "hidden"))

              .append(
                $("<button>").attr("class", "btn btn-default btn-cart-down")
                .append(
                  $("<span>").attr("class", "glyphicon glyphicon-chevron-down")))
              .append(
                $("<input>").addClass("item-quantity").attr("value", cart_item.quantity).attr("readonly", "readonly"))
              .append(
                $("<button>").attr("class", "btn btn-default btn-cart-up")
                .append(
                  $("<span>").attr("class", "glyphicon glyphicon-chevron-up")))
              .append(
                $("<button>").attr("class", "btn btn-default btn-cart-remove")
                .append(
                  $("<span>").attr("class", "glyphicon glyphicon-remove")))
                )
            ) // a
          ) // div
          .append(
            $("<div>").attr("class", "cart-details")
            .append(
              $("<span>").attr("class", "cart-package").append(package_mapper[cart_item.package_method]))
            .append(
              $("<span>").attr("class", "cart-price").append("$" + cart_item.price * cart_item.quantity))
          ) // div
        )
    });

  } else {
    $("#btn-checkout-cart").attr('disabled', true);
  };

  // Prevent shopping cart dropdown from closing on clicking inside
  $(document).on('click', '#shopping-cart .dropdown-menu', function (e) {
    e.stopPropagation();
  });

  var getScrWidth = function () { return $(window).width(); };
  var isMobile = function () { return getScrWidth() < 768; };

  // Dropdown open on hover
  $('.dropdown:not(#shopping-cart), .dropdown-submenu:not(#shopping-cart)')
    .mouseenter(function() {
      var $el = $(this);

      if (!isMobile()) {
        $el.children('.dropdown-menu').css('display', 'block');
        $el.addClass('open');
      }
    })
    .mouseleave(function() {
      var $el = $(this);

      if (!isMobile()) {
        $el.children('.dropdown-menu').css('display', 'none');
        $el.removeClass('open');
      }
    });

  $('#shopping-cart.dropdown')
    .mouseenter(function() {
      var $el = $(this);

      if (!isMobile()) {
        $el.find('.shopcart-summary .dropdown-menu').css('display', 'block');
        $el.addClass('open');
      }
    })
    .mouseleave(function() {
      var $el = $(this);

      if (!isMobile()) {
        $el.find('.shopcart-summary .dropdown-menu').css('display', 'none');
        $el.removeClass('open');
      }
    });

  $('#shopping-cart .dropdown-toggle').on('click', function (e) {
    var $el = $(this);

    if (isMobile()) {
      var $shopcart = $('#shopping-cart')

      if($shopcart.hasClass('open')) {
        $shopcart.removeClass('open');
      } else {
        $shopcart.addClass('open');
      }
    }
  });

  // Dropdown submenu
  $('.dropdown-submenu a.submenu').on('click', function(e) {
    var $el = $(this);

    if (!isMobile()) {
      $el.parent().siblings().find('.dropdown-menu').css('display', 'none');
      $el.next('ul').css('display', 'block');
    } else {
      $el.parent().siblings().find('.dropdown-menu').css('display', 'none');
      $el.next('ul').css('display', 'block');
    }

    e.stopPropagation();
    e.preventDefault();
  });

  $('.dropdown-toggle').on('click', function (e) {
    var $el = $(this);

    $('.dropdown-submenu .dropdown-menu').css('display', 'none');
    $el.parent().siblings().find('.dropdown-menu').css('display', 'none');
    $el.siblings('.dropdown-menu').css('display', 'block');
  });

  $("#menu-cart").on("click", ".btn-cart-down", function() {
    $qty = $(this).siblings("#menu-cart .item-quantity");
    coffee_id = $(this).siblings("input[name='coffee_id']").val();
    coffee_name = $(this).siblings("input[name='coffee_name']").val();
    brew_method = $(this).siblings("input[name='brew_method']").val();
    package_method = $(this).siblings("input[name='package_method']").val();
    price = $(this).siblings("input[name='price']").val();

    if ($qty.val() > 1) {
      var new_val = parseInt($qty.val()) - 1;
      var cart_list = JSON.parse(localStorage.getItem("cart"));

      $qty.val(new_val);
      $("#cart-" + coffee_id + brew_method + package_method + " .cart-price")
        .text("$" + parseInt(price) * parseInt(new_val));

      $.each(cart_list, function(i, cart_item) {
        if (cart_item.coffee_id == coffee_id
          && cart_item.brew_method == brew_method
          && cart_item.package_method == package_method) {
          cart_item.quantity = new_val;
          localStorage.setItem("cart", JSON.stringify(cart_list));
        };
      });

    };
  });

  $("#menu-cart").on("click", ".btn-cart-up", function() {
    $qty = $(this).prev("#menu-cart .item-quantity");
    coffee_id = $(this).siblings("input[name='coffee_id']").val();
    coffee_name = $(this).siblings("input[name='coffee_name']").val();
    brew_method = $(this).siblings("input[name='brew_method']").val();
    package_method = $(this).siblings("input[name='package_method']").val();
    price = $(this).siblings("input[name='price']").val();

    var new_val = parseInt($qty.val()) + 1;
    var cart_list = JSON.parse(localStorage.getItem("cart"));

    $qty.val(new_val);
    $("#cart-" + coffee_id + brew_method + package_method + " .cart-price")
      .text("$" + parseInt(price) * parseInt(new_val));

    $.each(cart_list, function(i, cart_item) {
      if (cart_item.coffee_id == coffee_id
        && cart_item.brew_method == brew_method
        && cart_item.package_method == package_method) {
        cart_item.quantity = new_val;
        localStorage.setItem("cart", JSON.stringify(cart_list));
      };
    });

  });

  $("#menu-cart").on("click", ".btn-cart-remove", function() {
    coffee_id = $(this).siblings("input[name='coffee_id']").val();
    coffee_name = $(this).siblings("input[name='coffee_name']").val();
    brew_method = $(this).siblings("input[name='brew_method']").val();
    package_method = $(this).siblings("input[name='package_method']").val();

    var index_to_delete;
    var cart_list = JSON.parse(localStorage.getItem("cart"));

    $.each(cart_list, function(i, cart_item) {
      if (cart_item.coffee_id == coffee_id
        && cart_item.brew_method == brew_method
        && cart_item.package_method == package_method) {
        index_to_delete = i;
      };
    });
    cart_list.splice(index_to_delete, 1);
    localStorage.setItem("cart", JSON.stringify(cart_list));
    $("#cart-" + coffee_id + brew_method + package_method).remove();

    // TODO: prevent cart menu from closing

    if (cart_list.length < 1) {
      $("#btn-checkout-cart").attr('disabled', true);
    }
  });

  $("#form-checkout").submit(function(e) {
    $(this).append(
      $("<input>").attr("type", "hidden")
        .attr("name", "storage")
        .val(JSON.stringify(localStorage))
      );

    return true;
  });

  updateBodyTopMargin();

});

/* change body:margin-top taking into account the nav & the topbar height. */
function updateBodyTopMargin() {
  var $navBar = $('.navbar-fixed-top'),
      navBarHeight = $navBar.outerHeight() - 2; // 2px just in case ;)
  lastWindowWidth = $(window).width();
  $('body').css('margin-top', navBarHeight);
  if (lastWindowWidth >= 768) {
    $('.sidemenu').css('height', 'calc(100vh - ' + navBarHeight + 'px)');
  } else {
    $('.sidemenu').css('height', 'auto');
  }
}

$(window).load(function() {
  updateBodyTopMargin();
});

$(window).on('resize', function() {
  if ($(window).width() !== lastWindowWidth) {
    updateBodyTopMargin();
  }
});
/* // body:margin-top */

