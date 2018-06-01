var reg_data = {
  "package":"WB",
  "interval":14,
  "different":true,
  "brew":0,
};

var FG_ONE_ID_PREFIX = '#fg_one-';
var FG_TWO_ID_PREFIX = '#fg_two-';

$(document).on('submit', '.js-update-address', update_address);

$(document).ready(function() {

  $('#submit-voucher').submit(apply_voucher);
  $('#login-form').submit(do_login);
  $("#form-add-subscription").submit(addSubscription);

  var hasVoucher = $('#voucher-input-0').val();
  if (hasVoucher) {
    $('#submit-voucher').submit();
  }

  $('#js-voucher-def-btn').click(add_default_voucher);

  $("#create-new-subscription").click(function() {
    var coffeeID = $(this).data("coffeeId");
    $('#reg-page__active-subs').hide();
    $("#subscription-form").show();
    $("#subscription-form>li").hide();
    $("#subscription-form>li:first-child").show();
    $("#subscription-form>li:first-child>p").text("");
    $("#subscription-form>li:first-child").css("list-style-type", "none");
  });

  reg_data['package'] = $('#subs-details-form .opt-pack.selected').data('value') || "PODS";


    $('.package_info p').addClass('hide')
    $('.package_info .'+reg_data['package']).removeClass('hide')

  //if (reg_data['package'] === 'GR') {
  // $("#p_brew_goal").removeClass("hide");
    // $("#brew_goal").html( $(".opt-brew.selected").data('title') );
  //} else if (reg_data['package'] === 'WB') {
  //  $("#p_wholebeans").removeClass("hide");
  //} else if (reg_data['package'] === 'BB') {
  //  $("#p_drip_bags").removeClass("hide");
  //} else {
  //  $('p_brew_bags').removeClass('hide');
  //}

  if (reg_data['package'] === 'GR' || reg_data['package'] === 'WB') {
    var packageWeight = IS_DISCOVERY_PACK ? '3 x 80g' : '200g';
    $('#qty').html(gettext(packageWeight + ' (makes at least 12 cups of coffee)'));
  } else if (reg_data['package'] === 'DR') {
    var packageWeight = IS_DISCOVERY_PACK ? '3 x 4' : '10 x 10g';
    $('#qty').html(gettext(packageWeight + ' coffee drip bags'));
  }

  $('#confirm-subs').click(function(event) {
    event.preventDefault();

    if (reg_data['package'] ==='GR' && (reg_data["brew"] === 7 || reg_data["brew"]===0)) {
       alert('Oops! Please tell us how you make your coffee so we can grind it to the right settings for you')
    } else {
        $('#subs-auth-form').removeClass('hidden');
        $('#subs-details-form').addClass('hidden');

        if (isAuthenticated === 'True') {
          $("#address-form").show();
          $(".address-list").append('<li data-addr-id="-1" data-subid="subs-addr-change" data-parent-id="addsub-modal-addr" class="selected"><div><p><b class="js-addr-name">Base address</b></p><p><small class="js-addr-recipient_name">' + base_address['customer_name'] + '</small></p><p class="js-addr-lines">' + base_address.line1 + ', ' + base_address.line2 + '<br />' + base_address.country + ' ' +  base_address.postcode + '</p></div><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></li>');
          $.each(addresses, function(i, val){ // pull addresses here
            $(".address-list").append('<li data-addr-id="' + val.id + '" data-subid="subs-addr-change" data-parent-id="addsub-modal-addr"><div><p><b class="js-addr-name">' + val.name + '</b></p><p><small class="js-addr-recipient_name">' + val.customer_name + '</small></p><p class="js-addr-lines">' + val.line1 + ', ' + val.line2 + '<br />' + val.country + ' ' +  val.postcode + '</p></div><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></li>')
          });
        }

        $('.js-reg-step-1__title').css('cursor', 'pointer');
        $('.js-reg-step-1__title').click(function(e) {
          // allow users return to first step only if they are on the second step
          if ($('#subs-details-form').hasClass('hidden') &&
              !$('#subs-auth-form').hasClass('hidden')) {
            $('#subs-auth-form').addClass('hidden');
            $('#subs-details-form').removeClass('hidden');
          }
        });

        $('#subs-details-label').removeClass('active');
        $('#subs-auth-label').addClass('active');
    }
  });

  $('#create-account-link').click(function() {
    $('#login-form').hide();
    $('#subscription-form').show();
  });

  $('#confirm-acct').click(function(event) {
    event.preventDefault();

    var form = $(this).closest('form')
    $.ajax({
      url: $(this).attr('action'),
      type: "POST",
      data: form.serialize() + "&array=" + JSON.stringify(reg_data),

      success: function(data) {
        if (data.length > 0) {
          var errors = jQuery.parseJSON(data);
          var fg, fg_id, err_msg;

          $('#subs-auth-form .form-group').removeClass('has-warning');
          $('#subs-auth-form .form-group .help-block').html('');

          for (err in errors) {
            if (errors.hasOwnProperty(err)) {
              fg_id = (FG_ONE_ID_PREFIX + err);
              fg = $(fg_id);
              err_msg = errors[err][0];

              fg.addClass('has-warning');

              if (err === '__all__') {
                $.notify({ message: err_msg }, { type: 'danger' });
              } else {
                $(fg_id + ' .help-block').html(err_msg);
              }
            }
          }
        } else {
          $('#subs-ship-form').removeClass('hidden');
          $('#subs-auth-form').addClass('hidden');

          $('#subs-auth-label').removeClass('active');
          $('#subs-ship-label').addClass('active');
        }
      },
    });

  });

  $('#confirm-ship').click(function(event) {
    event.preventDefault();

    var form = $(this).closest('form')
    $.ajax({
      url: $(this).attr('action'),
      type: "POST",
      data: form.serialize() + "&array=" + JSON.stringify(reg_data),

      success: function(data) {
        if (data.length > 0) {
          var errors = jQuery.parseJSON(data);

          var fg, fg_id, err_msg;

          $('#subs-ship-form .form-group').removeClass('has-warning');
          $('#subs-ship-form .form-group .help-block').html('');

          for (err in errors) {
            if (errors.hasOwnProperty(err)) {
              fg_id = (FG_TWO_ID_PREFIX + err);
              fg = $(fg_id);
              err_msg = errors[err][0];

              fg.addClass('has-warning');

              if (err === '__all__') {
                $.notify({ message: err_msg }, { type: 'danger' });
              } else if (err === 'postcode') {
                $(fg_id + ' .help-block').html(gettext('Please enter a valid postal code.'));
              } else {
                $(fg_id + ' .help-block').html(err_msg);
              }

            }
          }
        } else {
          if (event.target.dataset.credits === 'true') {
            $('#subs-ship-form > form').submit();
          } else {
            $('#subs-bill-form').removeClass('hidden');
            $('#submit-subs').removeClass('hidden');
            $('#subs-ship-form').addClass('hidden');

            $('#subs-ship-label').removeClass('active');
            $('#subs-bill-label').addClass('active');
          }
        }
      },
    });

  });

  $('.opt-pack').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value');
    reg_data['package'] = value;
    console.log(reg_data['package'])

    if (value === 'GR' || value === 'WB') {
      $("#p_drip_bags").addClass('hide');

      if (value === 'GR') {
        $("#p_wholebeans").addClass("hide");
        if (brew_title) {
          $("#p_brew_goal").removeClass('hide');
        }

        if (brew_title === 'None'){
          $("#brew_5").click();
        }
        $("#brew_goal").html(brew_title);

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

    $('.opt-pack').removeClass('selected');
    $(this).addClass('selected');
  });

  $('.opt-interval').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value');
    reg_data['interval'] = value;
    $('.opt-interval').removeClass('selected');
    $(this).addClass('selected');
  });

  $('.opt-diff').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value');
    reg_data['different'] = value;
    $('.opt-diff').removeClass('selected');
    $(this).addClass('selected');
  });

  $('.opt-brew').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value'),
        name = $(this).find('span').text(),
        src = $(this).find('img').attr('src'),
        $dropdown = $(this).closest('.dropdown'),
        $item = $dropdown.find('.btn .dropdown-item');
    console.log('opt-brew:', value, name);

    $item.find('img').attr('src', src);
    $item.find('span').text(name);

    brew_title = name;
    reg_data['brew'] = value;
    $("#brew_goal").html(name);

    $("#p_brew_goal").removeClass("hide");
    $("#GR").click();

    $dropdown.removeClass('open');
    $dropdown.parent().find('.dropdown-menu').hide();
  });

  if (show_active_subs === "True") {
    $.each($.parseJSON(active_subscriptions), function(i, val) {
      $('#reg-page__active-subs__container').append('<div class="radio"><label><input type="radio" name="dest-order" value="' + val[0] + '"><img src="' + val[2] + '"/><b>' + val[1] + '</b><span> to ' + val[3] + '</span></label></div>');
    });
  };

  if (show_sub_details === "True") {
    $("#subscription-form").show();
    $("#subscription-form>li").hide();
    $("#subscription-form>li:first-child").show();
    $("#subscription-form>li:first-child>p").text("");
    $("#subscription-form>li:first-child").css("list-style-type", "none");
    $('#confirm-subs').click(function() {
      $("#address-form").show();
    });
  };

});

$("#reg-page__active-subs__container").on("click", "div.radio", function(){
  $("#reg-page__active-subs button[type=submit]").prop("disabled", false);
});

function do_login(e) {
  e.preventDefault();
  var form = $(this).find('form'),
      $msg = $(this).find('.help-block');
  $.ajax({
    url: form.attr('action'),
    type: 'POST',
    dataType: "json",
    data: form.serialize(),
    success: function(data) {
      $('#user-addresses__add').find('[name="csrfmiddlewaretoken"]').val(data.token);
      $('#submit-voucher').find('[name="csrfmiddlewaretoken"]').val(data.token);
      $('#substitute-subscription-form').find('[name="csrfmiddlewaretoken"]').val(data.token);
      if (data.errors) {
        $msg.html(data.errors);
      } else if (data.active_subscriptions) {
        isAuthenticated = "True";
        base_address = data.base_address;
        addresses = data.addresses;
        console.log('isAuthenticated', isAuthenticated, '.');
        if ($.parseJSON(data.active_subscriptions).length > 0) {
          $('#login-form').hide();
          $.each($.parseJSON(data.active_subscriptions), function(i, val) {
            $('#reg-page__active-subs__container').append('<div class="radio"><label><input type="radio" name="dest-order" value="' + val[0] + '"><img src="' + val[2] + '"/><b>' + val[1] + '</b><span> to ' + val[3] + '</span></label></div>');
          });
          $('#reg-page__active-subs').show();
        } else {
          var params = { subscribe: 1, isNespresso: 0 };
          $(location).attr('href', '/coffees/' + coffeeID + "?" + $.param(params));
        }
      } else if (data.prepare_cart) {
        $('#login-form').hide();
        $("#address-form").show();
        $(".address-list").append('<li data-addr-id="-1" data-subid="subs-addr-change" data-parent-id="addsub-modal-addr" class="selected"><div><p><b class="js-addr-name">Base address</b></p><p><small class="js-addr-recipient_name">' + data.base_address.customer_name + '</small></p><p class="js-addr-lines">' + data.base_address.line1 + ', ' + data.base_address.line2 + '<br />' + data.base_address.country + ' ' +  data.base_address.postcode + '</p></div><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></li>')
        $.each(data.addresses, function(i, val){
          $(".address-list").append('<li data-addr-id="' + val.id + '" data-subid="subs-addr-change" data-parent-id="addsub-modal-addr"><div><p><b class="js-addr-name">' + val.name + '</b></p><p><small class="js-addr-recipient_name">' + val.customer_name + '</small></p><p class="js-addr-lines">' + val.line1 + ', ' + val.line2 + '<br />' + val.country + ' ' +  val.postcode + '</p></div><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></li>')
        });
      }
    },
  });
};


function apply_voucher(e) {
  e.preventDefault();
  var form = $(this).closest('form'),
      $msg = $('.js-voucher-msg'),
      $price = $('#price-current'),
      $inp = $('.voucher-input'),
      $btn = $('.js-voucher-btn'),
      $btnDef = $('#js-voucher-def-btn'),
      $overallCost = $("#overall-cost"),
      $shippingCost = $("#shipping-cost");

  $btn.html('<i class="fa fa-refresh fa-spin"></i> ' + gettext('Applying'));
  $btn.prop('disabled', true);
  $btnDef.prop('disabled', true);

  $.ajax({
    url: $(this).attr('action'),
    type: 'POST',
    data: form.serialize(),
    success: function(data) {
      if (data.found) {
        if (data.new_price !== '') {
          $price.html(data.new_price);
        }

        if (data.voucher === 'TAKEFIVE!') {
          $msg.html(gettext('Awesome! You get $5 off your first order!'));
        } else if (data.gift_voucher === true) {
          $msg.html(gettext('Hurray! This order will be on your amazing friend') + ', <b>' + data.gift_sender + '</b>!');
        } else if (data.referral_voucher === true) {
          $msg.html(gettext('You have been referred by a wonderful friend') + ' <b>' + data.referral_sender + '</b>. ' + gettext('Here is 50% off your first order!'));
        } else if (data.v60starter_kit_gift_voucher === true) {
          $msg.html(gettext('Great choice! Your first order comes with a free V60 Starter Kit!'));
        } else if (data.x80g_bag_gift_voucher === true) {
          $msg.html(gettext('Great choice! Your first order beings with a free 80G Bag!'));
        } else if (data.x3_drip_coffee_bags_gift_voucher === true) {
          $msg.html(gettext('Great choice! Your first order beings with 3 free Drip Coffee Bags!'));
        } else if (data.shotpods_box_gift_voucher === true) {
          $msg.html(gettext('Great choice! Your first order beings with a ShotPods Taster Box!'));
        } else if (data.worldwide_voucher === true) {
          $msg.html(gettext('Awesome! Your first order costs $') + '<b>' + data.new_price + '</b>!');
        } else if (data.cart_voucher === true) {
          $msg.html(gettext('Awesome! Your first order costs $') + '<b>' + data.new_price + '</b>!');
        } else if (data.aeropress_25_off === true) {
          $msg.html(gettext('Great! Your order will come with an Aeropress with your first bag of coffee at 25% off (Usual - S$82)'));
        } else if (data.huat18 === true) {
          $msg.html(gettext('Happy CNY! Your first order will come with a free gift :)'));
        } else {
          $msg.html(gettext('Awesome! Your first order costs $') + ' <b>' + data.new_price + '</b>!');
        }

        $overallCost.html( Math.ceil((parseFloat($price.html()) + (parseFloat($shippingCost.html()) || 0)) * 100 ) / 100 );

        if (data.credits > 0 ) {
          $('#bill-form').addClass('hide');
          $('#confirm-ship').html(gettext('Subscribe'));
          $('#confirm-ship').attr('data-credits', 'true');
          $('#subs-auth-form > form').attr('action', '/getstarted/register-credits/');
          $('#subs-ship-form > form').attr('action', '/getstarted/register-credits/');
        }
        $inp.prop('disabled', true);
        $btn.html(gettext('Applied'));

      }
      // not data.found
      else if (data.sg_only) {
        $msg.html('This voucher is applicable in Singapore only');
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html('Apply');
      } else if (data.subs_only) {
        $msg.html('Oops! This voucher code is only applicable for a subscription');
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html('Apply');
      } else if (data.special_only) {
        $msg.html('Sorry. This voucher code is only applicable for special edition coffee subscriptions');
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html('Apply');
      } else if (data.discovery_only) {
        $msg.html('Oops! this voucher code is only applicable for discovery programme subscriptions');
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html('Apply');
      } else if (data.basic_only) {
        $msg.html('Oops, this voucher code is not applicable for special edition coffee');
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html('Apply');
      } else if (data.sets_only) {
        $msg.html('This voucher is applicable for gift sets only');
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html('Apply');
      } else {
        $msg.html(gettext('Your voucher code could not be found'));
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html(gettext('Apply'));
      }
    },
    error: function() {
      $btn.prop('disabled', false);
      $btnDef.prop('disabled', false);
      $.notify({
        message: gettext('Sorry there was an error trying to update your subscription. Please try again later.')
      }, {
        type: 'danger'
      });
    }
  });
}

function add_default_voucher(e) {
  e.preventDefault();
  if (is_worldwide === true)
    $('.voucher-input').val('GLOBAL');
  else
    $('.voucher-input').val('TAKEFIVE!');
  $('#js-voucher-msg').html(gettext('Don’t worry! Here is $5 off your first order!'));
}

function update_address(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      addressName = $form.find('[name="name"]').val(),
      addressRecipientName = $form.find('[name="recipient_name"]').val(),
      addressLine1 = $form.find('[name="line1"]').val(),
      addressLine2 = $form.find('[name="line2"]').val(),
      // addressCountry = $form.find('[name="country"]').val(),
      addressPostcode = $form.find('[name="postcode"]').val(),
      addressID = $form.find('[name="address"]').val(),
      $addressItem = $('[data-addr-id="' + addressID + '"]');

  // console.log('addressID:', addressID,'$addressItem:', $addressItem);
  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      // console.log('data:::', data);

      $form.find('.form-group').removeClass('has-warning');
      $form.find('.form-group .help-block').html('');
      $submitBtn
        .prop('disabled', false)
        .html(submitBtnDefText);

      if (data.success) {
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });

        if (typeof addressID === 'undefined') {
          // console.log('new address!, addressID:', addressID);
          // new address

          // add new address in address list
          var newAddress = data.address,
              $addressList = $('.js-address-list');

          $addressItem = $addressList.find('[data-addr-id]:last').clone();
          $addressItem
            .attr('data-addr-id', newAddress.id)
            // .data('addrId', newAddress.id)
            .removeClass('selected');
          $addressItem.each(function(i, el) {
            $addressList[i].append(el);
          });

          // add edit form for new address
          var $addrBlock = $('#acct-addr'),
              $addrPanel = $addrBlock.find('.panel-default:first-child'),
              $addrEditBlock = $addrBlock.find('.js-acct-addr-edit:last').clone(),
              $addrEditForm = $addrEditBlock.find('form');

          $addrEditBlock.attr('data-addr', newAddress.id);
          $addrEditForm.find('[name="name"]').val(newAddress.name);
          $addrEditForm.find('[name="recipient_name"]').val(newAddress.recipient_name);
          $addrEditForm.find('[name="line1"]').val(newAddress.line1);
          $addrEditForm.find('[name="line2"]').val(newAddress.line2);
          $addrEditForm.find('[name="postcode"]').val(newAddress.postcode);
          $addrEditForm.find('[name="address"]').val(newAddress.id);
          $addrPanel.append($addrEditBlock);
        }

        $addressItem.find('.js-addr-name').text(addressName);
        $addressItem.find('.js-addr-recipient_name').text(addressRecipientName);
        $addressItem.find('.js-addr-lines').html(
          addressLine1 + ' ' + addressLine2 + ', <br/>' + addressPostcode  // addressCountry
        );

        // $('#acct-addr-change').collapse('show');
        $('#user-addresses__add').collapse('hide');
        // $('#acct-addr').find('.trans-toggle').addClass('hidden');
        $('.js-address-list li.selected').removeClass('selected');
        $('.js-address-list li[data-addr-id=' + data.address.id + ']').addClass('selected');
        $('#reg-page__user-addresses .view-toggle').removeClass('hidden');

      } else {
        var errors = data.errors;
        for (err in errors) {
          if (errors.hasOwnProperty(err)) {
            var fg = $('.form-group--' + err);
            var err_msg = errors[err][0];

            fg.addClass('has-warning');
            fg.find('.help-block').html(err_msg);
          }
        }
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to update your address. Please try again later.')
      }, {
        type: 'danger'
      });

      $submitBtn
        .prop('disabled', false)
        .html(submitBtnDefText);
    },
  });
}

$('.js-address-list').on('click', 'li', function () {
  var subid = $(this).data('subid');
  var parentId = $(this).data('parentId');
  var addrName = $(this).find('.js-addr-name').text();  // $(this).data('addrName');
  var addr = $(this).find('.js-addr-lines').text(); // $(this).data('addr');

  $('.js-address-list li[data-subid="' + subid + '"]').removeClass('selected');
  $(this).addClass('selected');

  $("#" + parentId + " .selected-addr .addr-name").text(addrName);
  $("#" + parentId + " .selected-addr .addr").text(addr);
});

$("#confirm-and-pay").click(function() {
  var addrId = $('.js-address-list li.selected').data("addrId");
  $("#confirm-and-pay").attr("href", "/getstarted/process-cart?addrId=" + addrId); //sorry
});

function addSubscription(e) {
  e.preventDefault();
  var form = $(this).closest('form');

  var addrID = $('.js-address-list li.selected').data("addrId");
  if ( isNespresso ) {
    reg_data["package"] = "PODS";
    reg_data["brew"] = 6;
  }
  $.ajax({
    url: form.attr("action"),
    type: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')},
    dataType: 'json',
    data: form.serialize() + "&subParams=" + JSON.stringify(reg_data) + "&addrID=" + addrID,
    success: function(data) {
      if (data.status == 'success') {
        $(location).attr("href", '/accounts/profile/');
      } else if (data.status == 'failed') {
      } else {
      }
    },
    error: function() {
      console.log('ajax error');
    },
  });
};
