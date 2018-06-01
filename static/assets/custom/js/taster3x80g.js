var reg_data = {
  "package":"WB",
  "interval":7,
  "different":false,
  "brew":1,
};

var FG_ONE_ID_PREFIX = '#fg_one-';
var FG_TWO_ID_PREFIX = '#fg_two-';


$(document).ready(function() {

  reg_data['package'] = $('#subs-details-form .opt-pack.selected').data('value');
  console.log(reg_data);

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
    $('#qty').html(gettext('200g (makes at least 12 cups of coffee)'));
  } else if (reg_data['package'] === 'DR') {
    $('#qty').html(gettext('10 x 10g coffee drip bags'));
  }
  // $("#GR").addClass("selected");
  $("#weekly").addClass("selected");
  $("#same").addClass("selected");

  $('#confirm-subs').click(function(event) {
    event.preventDefault();
    $('#subs-auth-form').removeClass('hidden');
    $('#subs-details-form').addClass('hidden');
    $('#subs-details-label').removeClass('active');
    $('#subs-auth-label').addClass('active');
  });

  $('#confirm-acct').click(function(event) {
    event.preventDefault();

    var form = $(this).closest('form')
    $.ajax({
      url: '',
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
      url: '',
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
          $('#subs-bill-form').removeClass('hidden');
          $('#submit-subs').removeClass('hidden');
          $('#subs-ship-form').addClass('hidden');

          $('#subs-ship-label').removeClass('active');
          $('#subs-bill-label').addClass('active');
        }
      },
    });

  });

  // $('#submit-voucher').click(function(event) {
  //   event.preventDefault();
  //   var form = $(this).closest('form')
  //   $.ajax({
  //     url: 'voucher/',
  //     type: "POST",
  //     data: form.serialize(),
  //     success: function(data) {
  //       console.log(data);

  //       if (data.found) {
  //         $("#voucher-input").val(data.voucher).prop('disabled', true);
  //         $("#voucher").val(data.voucher);
  //         $("#price-current").html(data.new_price);
  //         $('#submit-voucher')
  //           .prop('disabled', true)
  //           .html('Voucher applied.')

  //         $.notify({
  //           message: 'Your voucher code discount has been applied to your order.'
  //         }, {
  //           type: 'success'
  //         });
  //       } else {
  //         $("#voucher").val("");
  //         $.notify({
  //           message: 'Your voucher code could not be found.'
  //         }, {
  //           type: 'danger'
  //         });
  //       }
  //     },
  //     error: function() {
  //       $.notify({
  //         message: 'Sorry there was an error trying to update your subscription. Please try again later..'
  //       }, {
  //         type: 'danger'
  //       });
  //     }
  //   });
  // });

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

      $('#qty').html(gettext('200g (makes at least 12 cups of coffee)'));

    } else if (value === 'DR' ) {
      $("#p_brew_goal").addClass('hide');
      $("#p_wholebeans").addClass("hide");
      $("#p_drip_bags").removeClass('hide');
      $('#qty').html(gettext('10 x 10g coffee drip bags'));
    }

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
