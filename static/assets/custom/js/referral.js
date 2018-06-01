var CLIENT_ID = '838753040067-v9gsed6nca912ni5tmriom8u390voj2i.apps.googleusercontent.com',
    SCOPES = ['https://www.googleapis.com/auth/contacts.readonly'],
    MAX_NEED_INVITE = 20, //  friends needed to invite for get special surprise
    CONTACT_TPL = (
      '<li class="gcontacts__item">' +
        '<label class="gcontacts__item-label">' +
          '<input name="google_contacts" value="{name}:{email}" class="gcontacts__item-input" type="checkbox">' + 
          '<span class="gcontacts__item-name">{name}</span>' +
          '<span class="gcontacts__item-email">{email}</span>' +
        '</label>' +
      '</li>');

/* GOOGLE CONTACTS */
function google_auth() {
  var config = {
    client_id: CLIENT_ID,
    scope: 'https://www.googleapis.com/auth/contacts.readonly',
    immediate: false,
  };
  gapi.auth.authorize(config, function() {
    google_fetch(gapi.auth.getToken());
  });
}

function google_fetch(token) {
  $.ajax({
    url: 'https://www.google.com/m8/feeds/contacts/default/full?access_token=' + token.access_token + '&max-results=5000&v=3.0&alt=json',
    dataType: 'jsonp',
    success: insert_google_contacts,
  });
}

function insert_google_contacts(data) {
  var contacts = data.feed.entry,
      $msg = $('.js-invites-msg'),
      msg_error = gettext('Sorry there was a problem importing your contacts. Please try again later.');
  $('.js-list-gcontacts').empty();
  if (contacts.length > 0) {
    for (var i = 0; i < contacts.length; i++) {
      var person = contacts[i],
          name = person.title.$t,
          email = person.gd$email ? person.gd$email[0].address : undefined;
      if (name && email) {
        var contact = CONTACT_TPL.replace(RegExp('{name}', 'g'), name)
                                 .replace(RegExp('{email}', 'g'), email);
        $(contact).appendTo('.js-list-gcontacts');
      }
    }

    $('.gcontacts__item-input:checkbox').on('change', select_contact_evt);
    $('#modal-referral-email').modal('hide');
    $('#modal-referral-google-contacts').modal('show');
  } else {
    $msg.show();
    $msg.html(msg_error);
    setTimeout(function() {
      $msg.hide();
    }, 5000);
  }
}

function select_all(source) {
  $('.gcontacts__item-input').each(function( index ) {
    this.checked = source.checked;
    $(this).change();
  });
}

function select_contact_evt() {
  $(this).parents('.gcontacts__item').toggleClass('gcontacts__item--selected');
}
/* // GOOGLE CONTACTS */


function invite_friends(e) {
  e.preventDefault();
  var form = $(this).closest('form'),
      $msg = $('.js-send-email-invites-msg'),
      $inp = $('.js-email-invites-field'),
      $btn = $('.js-send-email-invites-btn'),
      msg_txt = '',
      msg_success = gettext(
        'THANK YOU FOR SHARING THE LOVE OF HOOK COFFEE AROUND!'),
      msg_def_error = gettext(
        'Sorry there was an error trying to send invites. Please try again later.'),
      msg_duplicates = gettext(
        'Oops, some of your friends have been invited before.<br/>' + 
        'You have invited <b>{friends_invited}</b> new friends!'),
      msg_stats = gettext(
        'You earned <b>{points_earned}</b> free beanie points ' +
        'for inviting <b>{friends_invited}</b> friends.');

  $btn.html('<i class="fa fa-refresh fa-spin"></i> ' + gettext('Sending'));
  $btn.prop('disabled', true);

  $.ajax({
    url: $(this).attr('action'),
    type: 'POST',
    data: form.serialize(),
    success: function(data) {
      // console.log('data:', data);
      if (data.success === true) {

        if (data.duplicates) {
          msg_txt += msg_duplicates;
        } else {
          msg_txt += msg_success;
        }

        msg_txt += '<br/>' + msg_stats;
        msg_txt = msg_txt.replace(RegExp('{points_earned}', 'g'), data.points_earned)
                         .replace(RegExp('{friends_invited}', 'g'), data.friends_invited);
        update_customer_ref_data(data.friends_invited, data.points_earned);
      } else {
        var msg_form_error = '';
        for (var err in data.errors) {
          msg_form_error += data.errors[err].join('<br/>') + '<br/>';
        }
        msg_txt = msg_form_error || msg_def_error;
      }
    },
    error: function() {
      $.notify({
        message: msg_error
      }, {
        type: 'danger'
      });
    },
    complete: function() {
      $msg.html(msg_txt).show();
      setTimeout(function() {
        $msg.hide();
      }, 7000);
      $btn.prop('disabled', false).html(gettext('SEND INVITES'));
    }
  });
}


function update_customer_ref_data(friends_invited, points_earned) {
  TOTAL_FRIENDS_INVITED += friends_invited || 0;
  TOTAL_POINTS_EARNED += points_earned || 0;
  TOTAL_INVITE_POINTS_EARNED += points_earned || 0;
  TOTAL_POINTS_HAVE += points_earned || 0;

  var current_invited = TOTAL_FRIENDS_INVITED % MAX_NEED_INVITE,
      $more_msg = $('.js-invite-more-msg');

  if (current_invited === 0) {
    $more_msg.show().siblings().hide();
  } else {
    $more_msg.hide().siblings().show();
  }

  $('.js-cur-friends-invited').text(current_invited);
  $('.js-cur-friends-needed').text(MAX_NEED_INVITE - current_invited);
  $('.js-total-friends-invited').text(TOTAL_FRIENDS_INVITED);
  $('.js-total-points-earned').text(TOTAL_POINTS_EARNED);
  $('.js-total-invite-points-earned').text(TOTAL_INVITE_POINTS_EARNED);
  $('.js-total-points-have').text(TOTAL_POINTS_HAVE);
  // $('.js-ref-progress-bar').width((100 / (MAX_NEED_INVITE / current_invited)).toString() +'%');
  
  var $ppc = $('.js-pie-chart'),
      percent = 100 / (MAX_NEED_INVITE / current_invited),
      deg = 360 * percent / 100;
  if (percent > 50) {
    $ppc.addClass('gt-50');
  } else {
    $ppc.removeClass('gt-50');
  }
  $('.js-pie-chart-fill').css('transform', 'rotate('+ deg +'deg)');
}


function copy_to_clipboard() {
  var $copy_btn = $('.js-copy-btn'),
      $ref_link = $('.js-ref-link');

  $ref_link.select();

  try {
    var successful = document.execCommand('copy');
    if (successful) {
      $copy_btn.text('Copied');
      setTimeout(function() {
        $copy_btn.text('Copy');
      }, 2000);
    }
  } catch (err) {}
}


function filter_by_contact(contacts_list, textbox, check_single_match) {
  return $(contacts_list).each(function() {
    var $list = $(this),
        contacts = [];
    $list.find('input').each(function() {
      var contact = $(this).val().split(':');
      contacts.push({
        name: contact[0],
        email: contact[1],
      });
    });
    $list.data('contacts', contacts);
    $(textbox).bind('change keyup', function() {
      var contacts = $list.empty().data('contacts'),
          search = $(this).val().trim(),
          regex = new RegExp(search, 'gi');
      $.each(contacts, function(i) {
        var contact = contacts[i],
            contact_html = CONTACT_TPL.replace(RegExp('{name}', 'g'), contact.name)
                                      .replace(RegExp('{email}', 'g'), contact.email);
        if (contact.name.match(regex) !== null || 
            contact.email.match(regex) !== null) {
          $list.append(contact_html);
        }
      });
      $('.gcontacts__item-input:checkbox').on('change', select_contact_evt);
      if ($list.is(':empty')) {
        var not_found_msg = gettext('Not found =( Spread the love to someone else!');
        $list.append('<li class="gcontacts__item-notfound">' + not_found_msg + '</li>');
      }
      if (check_single_match === true && $list.children().length === 1) {
        var match = $list.find('input').get(0);
        if (match) {
          match.checked = true;
          $(match).change();
        }
      }
    });            
  });
};

$('#modal-referral-google-contacts').on('show.bs.modal', function(e) {
  filter_by_contact($('.js-list-gcontacts'), $('.js-filter-gcontacts'), true);
})

$('#referral-emails-form').submit(invite_friends);
$('#referral-gcontacts-form').submit(invite_friends);


/* IMPORT GOOGLE CONTACTS BY PEOPLE.API  */
/*
function handleAuthClick(event) {
  gapi.auth.authorize(
    {
      'client_id': CLIENT_ID, 
      'scope': SCOPES,
      'immediate': false
    }, handleAuthResult);
  return false;
}

function handleAuthResult(authResult) {
  if (authResult && !authResult.error) {
    loadPeopleApi();
  } else {
    // show error
  }
}

function loadPeopleApi() {
  gapi.client.load('https://people.googleapis.com/$discovery/rest', 'v1', listConnectionNames);
}

function listConnectionNames() {
  var request = gapi.client.people.people.connections.list({
     'resourceName': 'people/me',
     'pageSize': 500,
     'requestMask.includeField': 'person.names,person.email_addresses',
   });

   request.execute(function(resp) {
     var connections = resp.connections;
     appendPre('Connections:');

     if (connections.length > 0) {
       for (i = 0; i < connections.length; i++) {
         var person = connections[i];
         if ((person.names && person.names.length > 0) && 
             (person.emailAddresses && person.emailAddresses.length > 0)) {
           appendPre(person.names[0].displayName + ' - ' + person.emailAddresses[0].value);
         }
       }
     } else {
       appendPre('No friends found.');
     }
   }); 
}

function appendPre(message) {
  var pre = document.getElementById('output');
  var textContent = document.createTextNode(message + '\n');
  pre.appendChild(textContent);
}
*/
/* // IMPORT GOOGLE CONTACTS BY PEOPLE.API  */
