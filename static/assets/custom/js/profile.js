
$('.pref-option').click(change_preferences);
$('.js-submit-voucher').submit(apply_voucher);
$('.js-update-profile').submit(update_profile);
$('.js-update-preferences').submit(update_preferences);
$(document).on('submit', '.js-update-address', update_address);
$('.js-delete-address').submit(delete_address);
$('.js-change-primary-address').submit(change_primary_address);
$('.js-change-order-address').submit(change_order_address);
$('.js-change-order-coffee').submit(change_order_coffee);
$('.js-create-order').submit(create_order);
$('.js-create-order-review').submit(create_order_review);
$('.js-create-redem').submit(create_redem);

$('.js-show-order-review-modal').click(show_review_modal);
$('.js-show-unsubscribe-modal').click(show_unsubscribe_modal);
$('.js-change-order-coffee-btn').click(show_change_coffee_modal);
$('.js-change-schedule-btn').click(show_schedule_modal);
$('.js-change-schedule-submit').click(submit_schedule_modal);
$('.js-skip-next-delivery-modal').click(submit_skip_next_delivery_modal);
$('.js-change-schedule').submit(change_schedule);


// Shipping frequency slider
function initSlider(selector, isNespresso) {
  var $freqSlider = $('#range-slider' + selector);
  var $handle;

  console.log('initSlider', $freqSlider);

  if (isNespresso) {
    var days_to_coffee = days_to_pods = {
        1: 40,
        2: 40,
        3: 40,
        4: 40,
        5: 40,
        6: 40,
        7: 40,
        8: 35,
        9: 32,
        10: 28,
        11: 10,
        12: 9,
        13: 9,
        14: 8,
        15: 7,
        16: 7,
        17: 7,
        18: 6,
        19: 6,
        20: 6,
        21: 5,
        22: 5,
        23: 5,
        24: 5,
        25: 5,
        26: 5,
        27: 4,
        28: 4,
        29: 4,
        30: 3,
    }
  } else {
    var days_to_coffee = days_to_cups = {
        1: 35,
        2: 32,
        3: 30,
        4: 27,
        5: 22,
        6: 18,
        7: 16,
        8: 14,
        9: 12,
        10: 11,
        11: 10,
        12: 9,
        13: 9,
        14: 8,
        15: 7,
        16: 7,
        17: 7,
        18: 6,
        19: 6,
        20: 6,
        21: 5,
        22: 5,
        23: 5,
        24: 5,
        25: 5,
        26: 5,
        27: 4,
        28: 4,
        29: 4,
        30: 3,
    }
  }

  $freqSlider.rangeslider({
      polyfill: false,
      onInit: function() {
          $handle = $('.rangeslider__handle', this.$range);
          updateHandle($handle[0], this.value);
          $("#frequency-days" + selector).html(this.value);
      }
  }).on('input', function() {
      updateHandle($handle[0], this.value);
      $("#frequency-days" + selector).html(this.value);
  });

  function updateHandle(el, val) {
      el.textContent = val;
      $("#frequency-cups" + selector).html(days_to_coffee[val]);
      $('.modal[style *="display: block;"]').find('.modal-footer #id_interval').val(val);
  }

  $(selector).rangeslider();
}

$('#addNewSubsBags').on('shown.bs.modal', function (e) {
  initSlider('-bags', isNespresso=false);
});

$('#addNewSubsPods').on('shown.bs.modal', function (e) {
  initSlider('-pods', isNespresso=true);
});



$('#submit-payment').click(function(event) {
  event.preventDefault();

  var form = $(this).closest('form')
  var $submit_profile = $('#submit-payment');

  $submit_profile.prop('disabled', true);
  $submit_profile.html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  $.ajax({
    url: '',
    type: "POST",
    data: form.serialize(),

    success: function(data) {
      $submit_profile.prop('disabled', false);
      $submit_profile.html(gettext('Save'));

      if (typeof data === 'string') {
        var errors = jQuery.parseJSON(data);
        var fg, fg_id, err_msg;
        console.log(errors);

        $('#user-profile .form-group').removeClass('has-warning');
        $('#user-profile .form-group .help-block').html('');

        for (err in errors) {
          if (errors.hasOwnProperty(err)) {
            fg_id = ('#id_' + err);
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
        $('#user-profile .form-group').removeClass('has-warning');
        $('#user-profile .form-group .help-block').html('');

        $.notify({
          message: data.message
        }, {
          type: 'success'
        });
      }


    },
    error: function(data) {
      $submit_profile.prop('disabled', false);
      $submit_profile.html(gettext('Save'));

      $.notify({
        message: gettext('Sorry there was an error trying to update your preferences. Please try again later.')
      }, {
        type: 'danger'
      });
    },
  });
});


function apply_voucher(e) {
  e.preventDefault();

  // Process voucher on the server
  var $form = $(this).closest('form');
      $submitBtn = $form.find('button[type="submit"]'),
      $input = $form.find('[name="voucher"]'),
      $helpBlock = $form.find('.help-block'),
      $priceBlock = $form.closest('.js-coffee-panel').find('.js-sub-price');

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i> ' + gettext('Applying'));

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),

    success: function(data) {
      console.log('data:', data);
      if (data.errors) {
        var err_msg = data.errors['voucher'][0];
        $submitBtn
          .prop('disabled', false)
          .html(gettext('Apply'));
        $helpBlock
          .removeClass('hide text-success')
          .addClass('text-danger')
          .text(err_msg);
      } else {
        $helpBlock
          .removeClass('hide text-danger')
          .addClass('text-success')
          .text(data.message);
        $priceBlock.text('S$' + data.price);
        $submitBtn.html(gettext('Applied'));
        $input.prop('disabled', true);
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to apply the voucher. Please try again later.')
      }, {
        type: 'danger'
      });
    },
  });
}


function update_profile(e) {
  e.preventDefault();
  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]');

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  // // dirty hack
  // var country_field = '&' + $.param(
  //   {'country': $(':disabled[name=country]').val()});

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    // data: form.serialize() + country_field,

    success: function(data) {
      $form.find('.form-group').removeClass('has-warning');
      $form.find('.form-group .help-block').html('');

      if (data.success) {
        if ($submitBtn.hasClass('hide-modal')) {
          $submitBtn.closest('.modal').modal('hide');
        }
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });
      } else {
        var errors = data.errors;

        for (err in errors) {
          if (errors.hasOwnProperty(err)) {
            var fg = $('.form-group--' + err);
            var err_msg = errors[err][0];

            fg.addClass('has-warning');
            fg.find('.help-block').html(err_msg);
            // if (err === 'postcode') {
            //   fg.find('.help-block').html(gettext('Please enter a valid postal code.'));
            // } else {
            //   fg.find('.help-block').html(err_msg);
            // }
          }
        }
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to update your profile. Please try again later.')
      }, {
        type: 'danger'
      });
    },
    complete: function(jqXHR, status) {
      $submitBtn
        .prop('disabled', false)
        .html(gettext('Save'));
    },
  });
}


function change_preferences(e) {
  e.preventDefault();
  var $subscription = $(this).closest('.js-curr-subscription'),
      value = $(this).data('value'),
      $days = $subscription.find('.interval-slider-days'),
      $cups = $subscription.find('.interval-slider-cups'),
      $slider = $subscription.find('[name="interval-slider"]'),
      $intervalInput = $subscription.find('[name="interval"]'),
      $brewInput = $subscription.find('[name="brew"]'),
      $packageInput = $subscription.find('[name="package"]'),
      intervalDays;
  // console.log('change_preferences:', e, value);

  if ($(this).hasClass('opt-interval')) {
    $intervalInput.val($days.text());
  } else if ($(this).hasClass('opt-pack')) {
    $packageInput.val(value);
    $subscription.find('.opt-pack').removeClass('selected');
    $(this).addClass('selected');

    //if (value === 'DR') {
    //  intervalDays = days_cups_map_bags[$cups.text()];
    //} else {
    //  intervalDays = days_cups_map[$cups.text()];
    //};
    $slider.data('package', value);
    $days.text(intervalDays);
    $intervalInput.val(intervalDays);
  } else if ($(this).hasClass('opt-brew')){
    $subscription.find('.opt-brew').removeClass('selected');
    $(this).addClass('selected');
    $brewInput.val(value);
  }
}


function update_preferences(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]');

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      console.log('data:::', data);
      if (data.success) {
        var messages = data.message;
        for (msg in messages) {
          if (messages.hasOwnProperty(msg)) {
            $.notify({
              message: messages[msg]
            }, {
              type: 'success',
              timer: '60000'
            });
          }
          setTimeout(function()
          {
            location.reload();  //Refresh page
          }, 6000);
        }
      } else {
        var errors = data.errors;
        for (err in errors) {
          if (errors.hasOwnProperty(err)) {
            var err_msg = errors[err][0];
            console.log('err_msg:', err_msg);
            $.notify({
              message: err_msg
            }, {
              type: 'danger'
            });
          }
        }
      }
      $submitBtn
        .prop('disabled', false)
        .html(gettext('Save'));
    },
    error: function(data) {
      $submitBtn
        .prop('disabled', false)
        .html(gettext('Save'));

      $.notify({
        message: gettext('Sorry there was an error trying to update your preferences. Please try again later.')
      }, {
        type: 'danger'
      });
    },
  });
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
      console.log('data:::', data);

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

        $('#acct-addr-change').collapse('show');
        $('#acct-addr').find('.trans-toggle').addClass('hidden');
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


function delete_address(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      $selectedAddr = $submitBtn
                      .closest('#acct-addr-change')
                      .find('li[data-subid="acct-addr-change"].selected'),
      addrId = $selectedAddr.data('addrId'),
      $sameAddrInOtherPlaces = $('.js-address-list li[data-addr-id="' + addrId + '"]');

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));
  $form.find('[name="address"]').val(addrId);

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      // console.log('data:', data);
      $submitBtn.prop('disabled', false).html(submitBtnDefText);

      if (data.success) {
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });

        $('#acct-addr-change').collapse('hide');
        $selectedAddr.remove();
        $sameAddrInOtherPlaces.remove();
        $baseAddress = $submitBtn
          .closest('#acct-addr-change')
          .find('li[data-subid="acct-addr-change"]')
          .first();
        // mark first (base) address as primary
        $baseAddress.addClass('selected');
        $('.js-primary-addr').html($baseAddress.find('.js-addr-lines').html());
      } else {
        $.notify({
          message: data.errors[0]
        }, {
          type: 'danger'
        });
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to delete your address. Please try again later.')
      }, {
        type: 'danger'
      });

      $submitBtn
        .prop('disabled', false)
        .html(submitBtnDefText);
    },
  });
}


function change_primary_address(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      $selectedAddr = $submitBtn
                      .closest('#acct-addr-change')
                      .find('li[data-subid="acct-addr-change"].selected');

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));
  $form.find('[name="address"]').val($selectedAddr.data('addrId'));

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      $submitBtn.prop('disabled', false).html(submitBtnDefText);

      if (data.success) {
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });

        $('#acct-addr-change').collapse('hide');
        $('.js-primary-addr').html($selectedAddr.find('.js-addr-lines').html());
      } else {
        $.notify({
          message: gettext('Sorry there was an error trying to update your address. Please try again later.')
        }, {
          type: 'danger'
        });
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to update your address. Please try again later.')
      }, {
        type: 'danger'
      });

      $submitBtn.prop('disabled', false).html(submitBtnDefText);
    },
  });
}


function change_order_address(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      $selectedAddr = $submitBtn
                        .closest('.js-subs-addr-change')
                        .find('li[data-subid="subs-addr-change"].selected'),
      orderID = $selectedAddr.data('orderId'),
      addressID = $selectedAddr.data('addrId'),
      addressName = $selectedAddr.find('.js-addr-name').text();

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  $form.find('[name="order"]').val(orderID);
  $form.find('[name="address"]').val(addressID);

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      $submitBtn.prop('disabled', false).html(submitBtnDefText);

      if (data.success) {
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });

        $submitBtn.closest('.js-subs-addr-change').collapse('hide');
        $('.js-sub-' + orderID).find('.js-curr-addr-name').text(addressName);
      } else {
        $.notify({
          message: gettext('Sorry there was an error trying to update your address. Please try again later.')
        }, {
          type: 'danger'
        });
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to update your address. Please try again later.')
      }, {
        type: 'danger'
      });

      $submitBtn.prop('disabled', false).html(submitBtnDefText);
    },
  });
}

function change_order_coffee(e) {
  e.preventDefault();

  var $modal = $(this).closest('.modal'),
      $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      orderID = $form.find('[name="order"]').val(),
      newCoffeeName = $form.data('coffeeName'),
      newCoffeeImg = $form.data('coffeeImg'),
      $subscription = $('.js-sub-' + orderID);

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      $submitBtn.prop('disabled', false).html(submitBtnDefText);
      if (data.success) {
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });

        $subscription.find('.js-coffee-name').text(newCoffeeName);
        $subscription.find('.js-coffee-img').attr('src', newCoffeeImg);
        $subscription.find('.js-sub-price').text('S$' + data.price);
        $modal.modal('hide');

      } else {
        $.notify({
          message: gettext('Sorry there was an error trying to update your order. Please try again later.')
        }, {
          type: 'danger'
        });
      }
    },
    error: function(data) {
      $.notify({
        message: gettext('Sorry there was an error trying to update your order. Please try again later.')
      }, {
        type: 'danger'
      });

      $submitBtn.prop('disabled', false).html(submitBtnDefText);
    },
  });
}

function change_schedule(e) {
  e.preventDefault();

  // var $modal = $(this).closest('.modal'),
  var $form = $(this).closest('form'),
      orderID = $form.find('[name="order"]').val(),
      event = $form.find('[name="event"]').val(),
      $subscription = $(this).closest('.js-curr-subscription'),
      $subBtns = $(this).closest('.panel-row').find('.js-sub-btn'),
      // $skipBtn = $subscription.find('.js-skip-next-delivery-btn'),
      // $changeScheduleBtn = $subscription.find('.js-change-schedule-btn'),
      oldShippingDate = moment($subscription.data('shippingDate'), 'DD/MM/YYYY'),
      newShippingDate = moment($form.find('[name="newDate"]').val(), 'DD/MM/YYYY');

  $subBtns.prop('disabled', true);

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      $subscription
        .find('.js-ship-tomorrow-btn')
        .prop('disabled', false);

      $subscription
        .find('.js-sched-details-date')
        .text(newShippingDate.format('MMMM, D (dddd)'));

      $.notify({
        message: gettext("Your subscription's shipping date has been changed.")
      }, {
        type: 'success'
      });

      Intercom('trackEvent', event, {
        'order': orderID,
        'old_date': oldShippingDate.unix(),
        'new_date': newShippingDate.unix(),
      });

    },
    error: function(error) {
      $subBtns.prop('disabled', false);
      $.notify({
        message: gettext('Sorry there was an error trying to update your subscription. Please try again later.')
      }, {
        type: 'danger'
      });
    },
  });
}


function create_order(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      $selectedAddr = $form.find('.js-address-list li.selected'),
      addressID = $selectedAddr.data('addrId') || '-1';
      brew_type = $form.find('.modal-footer #id_brew').val();
      package_type = $form.find('.modal-footer #id_package').val();
        console.log(brew_type)
        console.log(package_type)

  if (brew_type === '7' && package_type === 'GR') {
    alert('Oops! Please tell us how you make your coffee so we can grind it to the right settings for you')
  } else {
  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));
  $form.find('[name="address"]').val(addressID);

  console.log('Form to send:', $form);

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      console.log('data:', data);
      if (data.success) {
        location.reload();
        // $submitBtn.prop('disabled', false).html(submitBtnDefText);
      } else {
        $submitBtn.prop('disabled', false).html(submitBtnDefText);
        $.notify({
          message: gettext('Sorry there was an error trying to create order. Please try again later.')
        }, {
          type: 'danger'
        });
      }
    },
    error: function(error) {
      $submitBtn.prop('disabled', false).html(submitBtnDefText);
      $.notify({
        message: gettext('Sorry there was an error trying to create order. Please try again later.')
      }, {
        type: 'danger'
      });
    },
  });

  }
}


function create_order_review(e) {
  e.preventDefault();

  var $modal = $(this).closest('.modal'),
      $form = $modal.find('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      orderID = $form.find('[name="order"]').val(),
      coffeeID = $form.find('[name="coffee"]').val(),
      rating = $form.find('.form-star-review .fa-star.clr-me-p:last').data('value'),
      comment = $form.find('[name="comment"]').val();
      brew = $form.find('#review-brewmethod').text();

  // console.log('create review:', orderID, rating, review);
  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));
  $form.find('[name="rating"]').val(rating);

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      if (data.success) {
        update_order_review(orderID, coffeeID, rating, comment, brew);
        $form
          .find('.help-block')
          .removeClass('text-danger')
          .addClass('hide');

        $modal.modal('hide');
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });
      } else {
        var errors = data.errors;
        for (err in errors) {
          if (errors.hasOwnProperty(err)) {
            var $helpBlock = $('.help-block--' + err); // rating
            var err_msg = errors[err][0];
            $helpBlock
              .removeClass('hide text-success')
              .addClass('text-danger')
              .html(err_msg);
          }
        }
      }
    },
    error: function(error) {
      $.notify({
        message: gettext('Sorry there was an error trying to create review. Please try again later.')
      }, {
        type: 'danger'
      });
    },
    complete: function(jqXHR, status) {
      $submitBtn
        .prop('disabled', false)
        .html(submitBtnDefText);
    },
  });
}


function create_redem(e) {
  e.preventDefault();

  var $form = $(this).closest('form'),
      $submitBtn = $form.find('button[type="submit"]'),
      submitBtnDefText = gettext($submitBtn.text()),
      $redemBtns = $(this).closest('.js-rewards').find('button[type="submit"]');

  $submitBtn
    .prop('disabled', true)
    .html('<i class="fa fa-refresh fa-spin"></i>  ' + gettext('Saving'));

  $.ajax({
    url: $form.attr('action'),
    type: $form.attr('method'),
    data: $form.serialize(),
    success: function(data) {
      // console.log('data:', data);
      $submitBtn
        .prop('disabled', false)
        .html(submitBtnDefText);
      if (data.success) {
        TOTAL_POINTS_HAVE -= data.points_spent || 0;
        TOTAL_REDEEMED_POINTS += data.points_spent || 0;
        $redemBtns.each(function(i, el) {
          $btn = $(this);
          if ($btn.data('points') > TOTAL_POINTS_HAVE) {
            $btn.prop('disabled', true);
          } else {
            $btn.prop('disabled', false);
          }
        });
        $('.js-total-points-have').text(TOTAL_POINTS_HAVE);
        $('.js-total-points-redemed').text(TOTAL_REDEEMED_POINTS);
        $.notify({
          message: data.message
        }, {
          type: 'success'
        });
      } else {
        var errors = data.errors;
        for (msg in errors) {
          if (errors.hasOwnProperty(msg)) {
            $.notify({
              message: errors[msg]
            }, {
              type: 'danger',
              timer: '60000'
            });
          }
        }
      }
    },
    error: function(error) {
      $submitBtn
        .prop('disabled', false)
        .html(submitBtnDefText);
      $.notify({
        message: gettext('Sorry there was an error trying to create reward. Please try again later.')
      }, {
        type: 'danger'
      });
    },
    complete: function(jqXHR, status) {
      if ($submitBtn.data('freeBag')) {
        $submitBtn
          .prop('disabled', true)
          .html(submitBtnDefText);
      }
    },
  });
}


function update_order_review(orderID, coffeeID, rating, comment, brew) {
  var detailsBtn = $('.js-order-details[data-order-id="' + orderID + '"][data-coffee-id="' + coffeeID + '"]'),
      reviewBtns = $('.js-show-order-review-modal[data-order-id="' + orderID + '"][data-coffee-id="' + coffeeID + '"]');
  if (rating) {
    detailsBtn.data('orderRating', rating);
    reviewBtns.data('orderRating', rating);
  }
  if (comment) {
    detailsBtn.data('orderReview', comment);
    reviewBtns.data('orderReview', comment);
  }
  if (brew) {
    detailsBtn.data('orderReview', brew);
    reviewBtns.data('orderReview', brew);
  }
}


function show_review_modal(e) {
  var orderId = $(this).data('orderId'),
      coffeeId = $(this).data('coffeeId'),
      coffeeName = $(this).data('coffeeName'),
      orderRating = parseInt($(this).data('orderRating')),
      orderReview = $(this).data('orderReview'),
      target = $(this).data('target'),
      $starsBlock = $(target).find('.form-star-review'),
      $brewBlock = $(target).find('.brew-block button'),
      $ratedStarsBlock = $(target).find('.form-star-review-rated'),
      $reviewInput = $(target).find('[name="comment"]'),
      $submitBtn = $(target).find('button[type="submit"]');

  if (!isNaN(orderRating)) {
    var $lastStar = $ratedStarsBlock.find('[data-value="' + orderRating + '"]');
    $starsBlock.hide();
    $ratedStarsBlock.show();
    $lastStar
      .nextAll()
      .removeClass('clr-me-p')
      .switchClass('fa-star', 'fa-star-o');
    $lastStar
      .prevAll()
      .andSelf()
      .addClass('clr-me-p')
      .switchClass('fa-star-o', 'fa-star');
  } else {
    $starsBlock.show();
    $ratedStarsBlock.hide();
  }

  if (!isNaN(orderRating)) {
    $reviewInput.prop('disabled', true).val(orderReview);
    $submitBtn.prop('disabled', true);
    $brewBlock.prop('disabled', true);
  } else {
    $submitBtn.prop('disabled', false);
    $reviewInput.prop('disabled', false).val('');
    $brewBlock.prop('disabled', false);
  }

  $(target).find('[name="order"]').val(orderId);
  $(target).find('[name="coffee"]').val(coffeeId);
  $(target).find('.js-coffee-name').text(coffeeName);
}


function show_change_coffee_modal(e) {
  var orderId = $(this).data('orderId'),
      target = $(this).data('target');
  $(target).find('[name="order"]').val(orderId);
}


function show_unsubscribe_modal(e) {
  var orderId = $(this).data('orderId');
  $('#cancel-sub-modal').find('[data-order-id]').data('orderId', orderId);
}


function show_schedule_modal(e) {
  var $subscription = $(this).closest('.js-curr-subscription');
  var disabledDates = [
      moment($subscription.data('shippingDate'), 'DD/MM/YYYY'),
      // moment('26/12/2017', 'DD/MM/YYYY'),
    ]
  $('#change-sched-date-picker')
    .data('orderId', $subscription.data('orderId'))
    .datetimepicker({
      inline: true,
      format: 'dd/MM/YYYY',
      daysOfWeekDisabled: [0, 6],
      disabledDates: disabledDates,
      minDate: moment().add(1, 'days'),
    });
}


function submit_schedule_modal(e) {
  var $modal = $(this).closest('.modal'),
      $datePicker = $modal.find('#change-sched-date-picker'),
      orderId = $datePicker.data('orderId'),
      newDate = moment($datePicker.data('DateTimePicker').date()._d, 'ddd MMM DD YYYY'),
      $subscription = $('.js-sub-' + orderId),
      $form = $subscription.find('.js-change-schedule-btn').closest('.js-change-schedule');

  $form.find('[name="newDate"]').val(newDate.format('DD/MM/YYYY'));
  $form.submit();
  $modal.modal('hide');
}


function submit_skip_next_delivery_modal(e) {
  var $modal = $(this).closest('.modal'),
      orderId = $(this).data('orderId'),
      $subscription = $('.js-sub-' + orderId),
      $form = $subscription.find('.js-skip-next-delivery-btn').closest('.js-change-schedule');

  $form.submit();
  $modal.modal('hide');
}

$('.opt-interval').click(function(event) {
  if (this.name === 'interval-slider') {
    // only for bottled coffee, which doesn't have a slider
    return
  }
  console.log($(this).data('value'));
  event.preventDefault();
  var value = $(this).data('value');
  // reg_data['interval'] = value;
  console.log($(this).closest('.js-curr-subscription'));
  $(this).closest('.js-curr-subscription').find('[name="interval"]').val(value);
  $('.opt-interval').removeClass('selected');
  $(this).addClass('selected');
});

$(document).ready(function() {
  if (skip.length > 0) {
    alert(skip);
  }
});
