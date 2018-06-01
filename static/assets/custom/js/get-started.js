'user strict';

function scrollToSection (id, delay, speed) {
  var target = $(id);
  if (target.length) {
    setTimeout(function () {
      target.velocity('stop').velocity('scroll', { duration: 300 });
    }, delay || 50);
  }
}

$(document).ready(function(){
  var userInfo = {}; // FIXME: go localStorage

  if ($('#brew-method').hasClass('show')) {
    // update_progress_bar(17);
    view_step(1);
  } else if ($('#intro').hasClass('show')) {
    // introduction form has errors
    // update_progress_bar(85);
  } else if ($('#result').hasClass('show')) {
    $('.c-get-started-footer').addClass('hide');
    view_step(6);
    show_recommend_coffee();
  }

  // Get name and email info from intro
  $('#submit-email').click(function(event) {
    event.preventDefault();

    var name = $('#name-input').val();
    var email = $('#email-input').val();

    userInfo.name = name;
    userInfo.email = email;


    var $userData = $('#user_info');
    if ($userData.val() !== '') {
      userInfo = JSON.parse($userData.val());
      userInfo.name = name;
      userInfo.email = email;
      $userData.val(JSON.stringify(userInfo));
    }

    // update_progress_bar(100);

    $userData.val(JSON.stringify(userInfo));
    $('#submit-intro').submit();
  });

  // FB Login
  window.fbAsyncInit = function() {
        FB.init({
            appId      : '288894678127616',
            xfbml      : true,
            version    : 'v2.6'
        });
    };

    (function(d, s, id){
        var js, fjs = d.getElementsByTagName(s)[0];
        if (d.getElementById(id)) {return;}
        js = d.createElement(s); js.id = id;
        js.src = "//connect.facebook.net/en_US/sdk.js";
        fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));

    loginFB = function (){
        FB.login(function(response){
          // console.log(response);
          if (response.status === 'connected') {
            var accesstoken = response.authResponse.accessToken;
            var userid = response.authResponse.userID;

            FB.api('/me?fields=id,name,email',function(response){
              // console.log(response);

              var name = response.name;
              var email = response.email;

              $('#name-input').val(name);
              $('#email-input').val(email);
              $('#accesstoken').val(accesstoken);

              var $userData = $('#user_info');
              if ($userData.val() !== '') {
                userInfo = JSON.parse($userData.val());
                userInfo.name = name;
                userInfo.email = email;
                $userData.val(JSON.stringify(userInfo));
              }

              // update_progress_bar(100);

              $userData.val(JSON.stringify(userInfo));

              $('#submit-intro').submit();
            });
          }
        }, {scope: 'public_profile,email'});
    }


  // Get brewing method
  $('.method-item').click(function(event) {
    event.preventDefault();
    var method = $(this).data('method');
    var title = $(this).data('title');
    var csrf_token = $(this).data('token');

    // console.log('Method: ' + method);

    userInfo.brew_title = title;
    userInfo.default_pack = 'WB';

    var nonNespresso = [
      'aeropress-method',
      'espresso-method',
      'frenchpress-method',
      'drip-method',
      'stovetop-method',
      'cold-brew-method',
      1, 2, 3, 4, 5, 8,
    ];

    var nespresso = [
      'nespresso-method',
      6,
    ];

    var noEquipment = [
      'no-method',
      7,
    ];

    $('.method-item').removeClass('selected');
    $(this).addClass('selected');

    $('.no-equipments-desc').removeClass('show');
    if (nonNespresso.indexOf(method) !== -1) {
      userInfo.method = method;

      $('#sensory-taste-profile').addClass('show');
      $('.non-nespresso-desc').addClass('show');
      $('.flavour-list-wrapper').addClass('show');
      $('#submit-flavours').addClass('show');
      $('#btn-back-to-brew-flav').addClass('show');
      // update_progress_bar(34);
      view_step(2);

    } else if (noEquipment.indexOf(method) !== -1) {
      $('.submit-drip').click(function() {
        userInfo.method = 7;
        userInfo.default_pack = 'DR';

        // mark method item drip bag 'selected'
        $('.method-item').removeClass('selected');
				$('.method-item[data-method="2"]').addClass('selected');

        $('#sensory-taste-profile').addClass('show');
        $('.non-nespresso-desc').addClass('show');
        $('.flavour-list-wrapper').addClass('show');
        $('#submit-flavours').addClass('show');
        $('#btn-back-to-brew-flav').addClass('show');

        $('.no-equipments-desc').removeClass('show');
        // update_progress_bar(34);
        view_step(2);
      });

      $('#sensory-taste-profile').removeClass('show');
      $('.non-nespresso-desc').removeClass('show');
      $('.flavour-list-wrapper').removeClass('show');
      $('#submit-flavours').removeClass('show');
      $('#btn-back-to-brew-flav').removeClass('show');

      $('.no-equipments-desc').addClass('show');
      $('#btn-back-to-brew-drip').addClass('show');

    }
      else if (nespresso.indexOf(method) !== -1) {
        userInfo.method = method;

        $('#sensory-taste-profile').addClass('show');
        $('.non-nespresso-desc').addClass('show');
        $('.flavour-list-wrapper').addClass('show');
        $('#submit-flavours').addClass('show');
        $('#btn-back-to-brew-flav').addClass('show');

        $("#register-link").addClass('hide');
        $("#register-link-credits").addClass('hide');
        $("#register-link-nespresso").removeClass('hide');
        // update_progress_bar(34);
        view_step(2);
      }

    // $('#brew-method').removeClass('show');
    $('#sensory-taste-profile').addClass('show');
    scrollToSection('#sensory-taste-profile');
    // show_recommendations(csrf_token);
  });

  // Get flavour profile
  $('.flavour-item').click(function(event) {
    event.preventDefault();
    var item = $(this);
    var selectedClass = 'selected';
    var flavour = item.data('flavour');
    userInfo.flavour = userInfo.flavour || [];

    $("#flavour-error").html("</br>");

    // If no preference
    if (flavour === 7) {
      if (userInfo.flavour.indexOf(flavour) !== -1) {
        userInfo.flavour = [];
        item.removeClass(selectedClass);
        // $('.no-preference-message').addClass('hide');
        $('.no-preference-message').html('</br>');
      } else {
        userInfo.flavour = [flavour];
        $('.flavour-item').removeClass(selectedClass);
        item.addClass(selectedClass);
        // $('.no-preference-message').removeClass('hide');
        $('.no-preference-message').html(gettext('It is absolutely fine if you have no preference!'));
      }

      return;
    }

    // Can't choose anything else if 'no preference'
    // is selected
    if (userInfo.flavour.indexOf(7) !== -1) {
      return;
    }

    if (!item.hasClass(selectedClass)) {
      if (!userInfo.flavour) {
        userInfo.flavour = [flavour];
        item.addClass(selectedClass);
        return;
      }

      if(userInfo.flavour.length >= 3) {
        // $('#flavour-error').addClass('show');
        $('#flavour-error').html(gettext("Just choose up to three! Click Next when you're ready."));
        return;
      } else {
        // $('#flavour-error').removeClass('show');
        $('#flavour-error').html('</br>');
      }

      userInfo.flavour.push(flavour);
      item.addClass(selectedClass);
    } else {
      if (userInfo.flavour) {
        userInfo.flavour.pop(flavour);
        item.removeClass(selectedClass);
      }
    }

  });


  $('#submit-flavours').click(function(event) {
    event.preventDefault();

    if(!userInfo.flavour || userInfo.flavour.length < 1) {
      // $('#flavour-error').addClass('show');
      $('#flavour-error').html(gettext("Just choose up to three! Click Next when you're ready."));
      return;
    } else {
      // $('#flavour-error').removeClass('show');
      $('#flavour-error').html('</br>');
    }

    // $('#sensory-taste-profile').removeClass('show');

    if (userInfo.flavour.indexOf(7) !== -1) {
      $('.flavour-desc').addClass('hide');
    } else {
      $('.no-preference-desc').addClass('hide');
    }

    $('#intensity').addClass('show');
    scrollToSection('#intensity');

    // update_progress_bar(51);
    view_step(3);
  });

  $('#intensity-slider').change(function() {
    var intensity = $('#intensity-slider').slider('getValue');
    var i_info = $('#intensity-info');

    if (intensity === 1) {
      i_info.html(gettext('I like something light and crisp'));
    } else if (intensity === 3) {
      i_info.html(gettext('I like intensity, but not too much'))
    } else if (intensity === 5) {
      i_info.html(gettext('I like something strong and bold'))
    } else {
      i_info.html('</br>');
    }
  });

  // Get Intensity
  $('#submit-intensity').click(function(event) {
    event.preventDefault();

    userInfo.intensity = $('#intensity-slider').slider('getValue');

    // $('#intensity').removeClass('show');
    $('#recommendation').addClass('show');
    $('#processing').addClass('show');
    $('#result').removeClass('show');
    scrollToSection('#recommendation');
    // update_progress_bar(68);
    view_step(4);

    // Wait 3 seconds 'til revealing the result
    window.setTimeout(function() {
      $('#recommendation').removeClass('show');
      $('#processing').removeClass('show');
      $('#intro').addClass('show');
      // update_progress_bar(85);
      view_step(5);
    }, 3000);
  });

  $('#other-coffees').click(function() {
    $('#recommendation').removeClass('show');
    if (userInfo.method == '6') {
      // Nespresso Pods
      $('#our-pods').addClass('show');
      $('#our-pods .isotope').isotope({
        itemSelector: '.element-item',
        layoutMode: 'masonry',
        percentPosition: true,
        filter: ':not(.no-equipments)',
        fitRows: {
          gutter: '.gutter-sizer'
        }
      });
    } else {
      // Coffee Bags
      $('#our-bags').addClass('show');
      $('#our-bags .isotope').isotope({
        itemSelector: '.element-item',
        layoutMode: 'masonry',
        percentPosition: true,
        filter: ':not(.no-equipments)',
        fitRows: {
          gutter: '.gutter-sizer'
        }
      });
    }
    $('#get-started-container').css({
      height: 'auto',
      display: 'block'
    });
  });

  // Choose another coffee
  $('.btn-choose-coffee').click(function(event) {
    event.preventDefault();

    $('#get-started-container').css({
      height: '100vh',
      display: 'flex'
    });

    var form = $(this).closest('form');
    $.ajax({
      url: 'another/',
      type: 'POST',
      data: form.serialize() + "&array=" + JSON.stringify(userInfo),

      success: function(data) {
        // console.log(data);
        $("#result #result-name").html(data.coffee);
        $("#result img").attr("src", data.img);
        $("#result .coffee-title").html(data.coffee);
        $("#result #description").html(data.description);
        $(".username").html(data.name);
      },
    });
    $('#our-bags').removeClass('show');
    $('#our-pods').removeClass('show');
    $('#recommendation').addClass('show');

  });


  $(".btn-back-to-voucher").click(function(event){
    // $('#voucher-input').val('');
    // $('#voucher-errors').html('</br>');

    $('#voucher-applied').removeClass('show');
    $('#brew-method').removeClass('show');
    $('#voucher').addClass('show');
  });

  $("#btn-back-to-brew-drip").click(function(event){
    event.preventDefault();
    scrollToSection('#brew-method');
    // $('#sensory-taste-profile').removeClass('show');
    // $('.no-equipments-desc').removeClass('show');
    // $('#brew-method').addClass('show');
    // update_progress_bar(17);
  });

  $("#btn-back-to-brew-flav").click(function(event){
    event.preventDefault();
    scrollToSection('#brew-method');
    // $('#sensory-taste-profile').removeClass('show');
    // $('#brew-method').addClass('show');
    // update_progress_bar(17);
  });

  $("#btn-back-to-flavours").click(function(event){
    event.preventDefault();
    scrollToSection('#sensory-taste-profile');
    $('.no-preference-message').html('</br>');

    // $('#sensory-taste-profile').addClass('show');
    // $('.no-preference-message').addClass('hide');
    // $('#intensity').removeClass('show');
    // update_progress_bar(34);
  });


  // function show_recommendations(csrf_token) {
  //   $('#recommendation').addClass('show');
  //   update_progress_bar(100);
  //   view_step(5);

  //   // Process userInfo on the server
  //   $.ajax({
  //     url: 'recommend/',
  //     type: "POST",
  //     data: {
  //       csrfmiddlewaretoken: csrf_token,
  //       array: JSON.stringify(userInfo)
  //     },
  //     success: function(data) {
  //       $("#result #result-name").html(data.coffee);
  //       $("#result img").attr("src", data.img);
  //       $("#result .coffee-title").html(data.coffee);
  //       $("#result #description").html(data.description);
  //       $(".username").html(data.name);
  //       userInfo.name = data.name;
  //       userInfo.email = data.email;
  //     },
  //   });
  //   // Wait 3 seconds 'til revealing the result
  //   window.setTimeout(function() {
  //     $('#processing').removeClass('show');
  //     $('.c-get-started-footer').addClass('hide');
  //     $('#result').addClass('show');
  //   }, 3000);
  // }

  function show_recommend_coffee() {
    var csrftoken = $('#csrftoken').val();
    $.ajax({
      url: 'recommend/',
      type: 'POST',
      data: {
        csrfmiddlewaretoken: csrftoken
      },
      success: function(data) {
        $("#result #result-name").html(data.coffee);
        $("#result img").attr("src", data.img);
        $("#result .coffee-title").html(data.coffee);
        $("#result #description").html(data.description);
        $(".username").html(data.name);

        // show all sections after refresh
        $("#brew-method").addClass('show');

        $("#sensory-taste-profile").addClass('show');
        $(".non-nespresso-desc").addClass('show');
        $('#submit-flavours').addClass('show');
        $('#btn-back-to-brew-flav').addClass('show');

        $("#intensity").addClass('show');

        // scroll down to #recommendation
        scrollToSection('#recommendation', 0, 200);

        // userInfo.name = data.name;
        // userInfo.email = data.email;
        if (data.brew_method === 6) { 
          userInfo.method = '6';
          $("#register-link-nespresso").removeClass('hide');
        } else {
          $("#register-link").removeClass('hide');
        }
      },
    });
  }
});

// Initialize Slider
$(document).ready(function(){
  var mySlider = $('#intensity-slider').slider({
    min: 1,
    max: 5,
    value: 3,
    tooltip: 'hide',
    orientation: 'horizontal',
  });

  var colors = [ '#CA9081','#9C6F63','#755248', '#4E3631', '#332420' ];
  mySlider.on('slide', function(slider) {
    var color = colors[slider.value - 1];
    $('.coffee-cup').css('color', color);
  });
});


function update_progress_bar(val) {
  $('.js-progress-bar--get-started').width(val.toString() +'%');
}

function view_step(step) {
  var path = '/reg_step_' + step.toString();
  ga('send', 'pageview', path);
}
