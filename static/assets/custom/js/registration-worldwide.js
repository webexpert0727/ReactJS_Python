var FG_ONE_ID_PREFIX = '#fg_one-';
var FG_TWO_ID_PREFIX = '#fg_two-';

$(document).ready(function() {
  $('#js-voucher-def-btn').click(add_default_voucher);
  $('.submit-voucher').submit(apply_voucher);

  if (isAuthenticated === 'True') {
    $("#address-form").show();
    $(".address-list").append('<li data-addr-id="-1" data-subid="subs-addr-change" data-parent-id="addsub-modal-addr" class="selected"><div><p><b class="js-addr-name">Base address</b></p><p><small class="js-addr-recipient_name">' + base_address['customer_name'] + '</small></p><p class="js-addr-lines">' + base_address.line1 + ', ' + base_address.line2 + '<br />' + base_address.country + ' ' +  base_address.postcode + '</p></div><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></li>');
    $.each(addresses, function(i, val){ // pull addresses here
      $(".address-list").append('<li data-addr-id="' + val.id + '" data-subid="subs-addr-change" data-parent-id="addsub-modal-addr"><div><p><b class="js-addr-name">' + val.name + '</b></p><p><small class="js-addr-recipient_name">' + val.customer_name + '</small></p><p class="js-addr-lines">' + val.line1 + ', ' + val.line2 + '<br />' + val.country + ' ' +  val.postcode + '</p></div><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></li>')
    });
  }

  $('#confirm-acct').click(function(event) {
    event.preventDefault();

    var form = $(this).closest('form')

    $.ajax({
      url: form.attr('action'),
      type: "POST",
      data: form.serialize(),

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
    if (is_worldwide === "") $("#fg_two-country").hide();
  });

  $('#confirm-ship').click(function(event) {
    event.preventDefault();

    var form = $(this).closest('form')

    $.ajax({
      url: form.attr('action'),
      type: "POST",
      data: form.serialize(),

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

              if (err === 'postcode') {
                $(fg_id + ' .help-block').html('Please enter a valid postal code.');
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

  $("#id_two-country").on("change", function(){
    var coffee_ids = [];
      $.each(JSON.parse(localStorage.getItem("cart")), function(i, cart_item) {
        coffee_ids.push({'id':cart_item.coffee_id, 'qty':cart_item.quantity});
        });
      var data = {
          'cid': this.value,
          'coffee_ids': coffee_ids,
        };
      console.log('get_shipping_rates', data);
      $.ajax({
        url: "/coffees/get_shipping_rates/",
        dataType: 'json',
        type: "POST",
        headers: {'X-CSRFToken': getCookie('csrftoken')},
        data: {'my_data': JSON.stringify(data)},
        success: function(response) {
            console.log('response', response);
            $("#shipping-cost").text(response.shipping_cost);
            $("#fg_two-country>.help-block").text("$" + response.shipping_cost);
            $("#overall-cost").text(
              Math.ceil((parseFloat($("#price-current").text()) + parseFloat($("#shipping-cost").text())) * 100) / 100
              );
        },
    });
    // console.log(this.value);
    //     $.ajax({
    //       url: "/coffees/get_shipping_rates/",
    //       dataType: 'json',
    //       data: {
    //         'cid': this.value,
    //       },
    //       success: function(response) {
    //         console.log('response', response);
    //         $("#shipping-cost").text(response.shipping_cost);
    //         $("#fg_two-country>.help-block").text("$" + response.shipping_cost);
    //         $("#overall-cost").text(parseFloat($("#price-current").text()) + parseFloat($("#shipping-cost").text()));
    //       },

    //     }); // ajax
  });

});
