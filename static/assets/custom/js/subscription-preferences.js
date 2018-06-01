$(document).ready(function(){
  // defaults
  var subPref = {
    'package': 'Ground',
    'interval': 7,
    'different': false
  };

  $('.opt-pack').click(function(event) {
    var packaging = $(this).data('value');
    subPref['package'] = packaging;
  });

  $('.opt-interval').click(function(event) {
    var interval = $(this).data('value');
    subPref['interval'] = parseInt(interval);
  });

  $('.opt-diff').click(function(event) {
    var different = $(this).data('value');
    subPref['package'] = different;
  });
});
