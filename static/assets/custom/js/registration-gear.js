var FG_ONE_ID_PREFIX = '#fg_one-';
var FG_TWO_ID_PREFIX = '#fg_two-';


$(document).ready(function() {

  $('#confirm-acct').click(function(event) {
    event.preventDefault();

    var form = $(this).closest('form')
    $.ajax({
      url: $(this).attr('action'),
      type: "POST",
      data: form.serialize(),

      success: function(data) {
        console.log('data:', data);
        if (data.success !== true) {
          var errors = data;
          console.log('errors', errors);
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
      data: form.serialize(),

      success: function(data) {
        console.log('data:', data);
        if (data.success !== true) {
          var errors = data;
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



});
