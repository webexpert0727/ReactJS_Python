$(document).ready(function() {

    var brew_method = "None";
    var package_method = "WB";

    $('#brew_goal').html(brew_method);
    if (package_method === 'GR') {
        $('#p_brew_goal').removeClass('hide');
    }
    if (brew_method === 'Drip') {
        $('#p_drip_bags').removeClass('hide');
    }

    $('.opt-brew').click(function(event) {
      event.preventDefault();
      $('#p_forgot_methods').addClass('hide');
      $('#p_forgot_package').addClass('hide');
      $('#p_forgot_brew').addClass('hide');
      var value = $(this).data('value');
      var title = $(this).data('title');
      console.log(value);
      brew_method = title;
      $('#brew_goal').html(brew_method);
      $('[name="brew-method"]').val(value);
      $('.opt-brew').removeClass('selected');
      $(this).addClass('selected');
      if (title === 'None'){
        $('#p_brew_goal').addClass('hide');
        $('#p_drip_bags').removeClass('hide');

        $('#pack_DR').click();
      }
    });

    $('.opt-pack').click(function(event) {
      event.preventDefault();
      $('#p_forgot_methods').addClass('hide');
      $('#p_forgot_package').addClass('hide');
      $('#p_forgot_brew').addClass('hide');
      var value = $(this).data('value');
      console.log(value);
      package_method = value;
      $('[name="package-method"]').val(value);
      $('.opt-pack').removeClass('selected');
      $(this).addClass('selected');

    if (value === 'GR' || value === 'WB') {
      $("#p_drip_bags").addClass('hide');

      if (value === 'GR') {
        $("#p_wholebeans").addClass("hide");
        $("#p_brew_goal").removeClass('hide');

        if (brew_method === 'None'){
          $("#brew_Drip").click();
          console.log("Selected " + brew_method);
        }
        $("#brew_goal").html(brew_method);

      } else {
        $("#p_brew_goal").addClass('hide');
        $("#p_wholebeans").removeClass("hide");
      }

      var packageWeight = IS_DISCOVERY_PACK ? '3 x 80g' : '200g';
      $('#qty').html(gettext(packageWeight + ' (makes at least 12 cups of coffee)'));

    } else if (value === 'DR' ) {
      var packageWeight = IS_DISCOVERY_PACK ? '3 x 4' : '10 x 10g';
      $("#p_brew_goal").addClass('hide');
      $("#p_wholebeans").addClass("hide");
      $("#p_drip_bags").removeClass('hide');
      $('#qty').html(gettext(packageWeight + ' coffee drip bags'));
    }

    });

    $("#modal-cart-add .btn-cart-down").click(function() {
        $qty = $(this).next("input#item-quantity");
        if ($qty.val() > 1) {
            $qty.val($qty.val() - 1);
            $("#modal-cart-add #item-quantity").val($qty.val());
        };
    });

    $("#modal-cart-add .btn-cart-up").click(function() {
        $qty = $(this).prev("input#item-quantity");
        $qty.val(parseInt($qty.val()) + 1);
        $("#modal-cart-add #item-quantity").val($qty.val());
    });

})
