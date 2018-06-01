var reg_data = {
  "package":"PODS",
  "interval":14,
  "different":true,
  "brew":1,
};

var FG_ONE_ID_PREFIX = '#fg_one-';
var FG_TWO_ID_PREFIX = '#fg_two-';

if ($("#ex6").length) {
  var slider = new Slider("#ex6");
};

$(document).ready(function() {

  $('#submit-voucher').submit(apply_voucher);

  var hasVoucher = $('#voucher-input').val();
  if (hasVoucher) {
    $('#submit-voucher').submit();
  }

  $('#js-voucher-def-btn').click(add_default_voucher);

  // reg_data['package'] = $('#subs-details-form .opt-pack.selected').data('value');
  // console.log(reg_data);

  if (reg_data['package'] === 'GR') {
    $("#p_brew_goal").removeClass("hide");
    $("#brew_goal").html( $(".opt-brew.selected").data('title') );
  } else if (reg_data['package'] === 'WB') {
    console.log('whOLeBEAns');
    $("#p_wholebeans").removeClass("hide");
  } else {
    console.log('dRIpbaGs');
    $("#p_drip_bags").removeClass("hide");
  }

  if (reg_data['package'] === 'GR' || reg_data['package'] === 'WB') {
    var packageWeight = IS_DISCOVERY_PACK ? '3 x 80g' : '200g';
    $('#qty').html(gettext(packageWeight + ' (makes at least 12 cups of coffee)'));
  } else if (reg_data['package'] === 'DR') {
    var packageWeight = IS_DISCOVERY_PACK ? '3 x 4' : '10 x 10g';
    $('#qty').html(gettext(packageWeight + ' coffee drip bags'));
  } else if (reg_data['package'] === 'PODS') {
    $('#qty').html(gettext('20 Nespresso<span class="registered-sign"></span> compatible pods'));
  }
  // $("#GR").addClass("selected");
  $("#weekly").addClass("selected");
  // $("#same").addClass("selected");

  $('#confirm-subs').click(function(event) {
    event.preventDefault();
    $('#subs-auth-form').removeClass('hidden');
    $('#subs-details-form').addClass('hidden');
    $('#subs-details-label').removeClass('active');
    $('#subs-auth-label').addClass('active');
  });

  $('#confirm-acct').click(function(event) {
    event.preventDefault();
    reg_data['package'] = $('#subs-details-form .opt-pack.selected').data('value') || "PODS";
    var form = $(this).closest('form')
    $.ajax({
      url: $(this).attr('action'),
      type: "POST",
      data: form.serialize() + "&array=" + JSON.stringify(reg_data),

      success: function(data) {
        if (data.length > 0) {
          var errors = jQuery.parseJSON(data);
          // console.log(errors);
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
          console.log(errors);

          var fg, fg_id, err_msg;

          $('#subs-ship-form .form-group').removeClass('has-warning');
          $('#subs-ship-form .form-group .help-block').html('');

          for (err in errors) {
            if (errors.hasOwnProperty(err)) {
              fg_id = (FG_TWO_ID_PREFIX + err);
              fg = $(fg_id);
              err_msg = errors[err][0];

              fg.addClass('has-warning');

              if (err === 'postcode') {
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

    if (value === 'GR' || value === 'WB') {
      $("#p_drip_bags").addClass('hide');

      if (value === 'GR') {
        $("#p_wholebeans").addClass("hide");
        $("#p_brew_goal").removeClass('hide');

        if (brew_title === 'None'){
          $("#brew_5").click();
          console.log("Selected " + brew_title);
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


    if ($("#ex6").length) {
      if (value !== "DR") {
        interval_days = days_cups_map[interval_cups];
        // console.log('New: ' + cups_days_map[reg_data['interval']]);
        // slider.setValue(parseInt(cups_days_map[reg_data['interval']]));
        // $('#ex6SliderVal').text(cups_days_map[reg_data['interval']]);
      } else {
        interval_days = days_cups_map_bags[interval_cups];
        // console.log('New: ' + cups_days_map_bags[reg_data['interval']]);
        // slider.setValue(parseInt(cups_days_map_bags[reg_data['interval']]));
        // $('#ex6SliderVal').text(cups_days_map_bags[reg_data['interval']]);
      };

      $('#interval-slider-days').text(interval_days);
      reg_data['interval'] = interval_days;
    };

    console.log(reg_data);
    $('.opt-pack').removeClass('selected');
    $(this).addClass('selected');
  });

  $('.opt-interval').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value');
    reg_data['interval'] = value;
    console.log(reg_data);
    $('.opt-interval').removeClass('selected');
    $(this).addClass('selected');
  });

  $('.opt-diff').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value');
    reg_data['different'] = value;
    console.log(reg_data);
    $('.opt-diff').removeClass('selected');
    $(this).addClass('selected');
  });

$('.opt-brew').click(function(event) {
    event.preventDefault();
    var value = $(this).data('value');
    var title = $(this).data('title');

    if (title == 'None') {
      $("#DR").click();
    }

    brew_title = title;
    reg_data['brew'] = value;
    console.log(reg_data);
    $('.opt-brew').removeClass('selected');
    $(this).addClass('selected');
    $("#brew_goal").html(title);
  });

});


function apply_voucher(e) {
  e.preventDefault();
  var form = $(this).closest('form'),
      $msg = $('#js-voucher-msg'),
      $price = $('#price-current'),
      $inp = $('#voucher-input'),
      $btn = $('#js-voucher-btn'),
      $btnDef = $('#js-voucher-def-btn');

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
          $msg.html(gettext('Great choice! Your first order beings with a Shotpods Taster Box!'));
        } else if (data.aeropress_25_off === true) {
          $msg.html(gettext('Great! Your order will come with an Aeropress with your first bag of coffee at 25% off (Usual - S$82)'));
        } else if (data.huat18 === true) {
          $msg.html(gettext('Happy CNY! Your first order will come with a free gift :)'));
        } else {
          $msg.html(gettext('Awesome! Your first order costs') + '<b>' + data.new_price + '</b>!');
        }

        if (data.credits > 0 ) {
          console.log('Credits:', data.credits);
          $('#bill-form').addClass('hide');
          $('#confirm-ship').html(gettext('Subscribe'));
          $('#confirm-ship').attr('data-credits', 'true');
          $('#subs-auth-form > form').attr('action', '/getstarted/register-credits/');
          $('#subs-ship-form > form').attr('action', '/getstarted/register-credits/');
        } else {
          console.log('No credits');
        }

        $inp.prop('disabled', true);
        $btn.html(gettext('Applied'));

        // $.notify({
        //   message: 'Your voucher code discount has been applied to your order.'
        // }, {
        //   type: 'success'
        // });

      } else {
        $msg.html(gettext('Your voucher code could not be found.'));
        $btn.prop('disabled', false);
        $btnDef.prop('disabled', false);
        $btn.html(gettext('Apply'));
        // $("#voucher").val("");
        // $.notify({
        //   message: 'Your voucher code could not be found.'
        // }, {
        //   type: 'danger'
        // });
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
  $('#voucher-input').val('TAKEFIVE!');
  $('#js-voucher-msg').html(gettext('Don’t worry! Here is $5 off your first order!'));
}
