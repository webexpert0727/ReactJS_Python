window.fbAsyncInit = function() {
  FB.init({
    appId   : '1717461351840123', // local: 1742474879359316 test: 1097894933625398 live: 1717461351840123
    status  : true,
    cookie  : true,
    xfbml   : true,
    version : 'v2.7'
  });
};

(function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s); js.id = id;
  js.src = "//connect.facebook.net/en_US/sdk.js";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));


function fb_share(e) {
  e.preventDefault();
  FB.ui({
    method: 'feed',
    link: 'https://hookcoffee.com.sg/',
    picture: 'https://hookcoffee.com.sg' + e.target.dataset.picture,
    name: e.target.dataset.name,
    description: e.target.dataset.description,
    caption: e.target.dataset.caption,
    hashtag: e.target.dataset.hashtag
  }, function(response) {
    if (response && response.post_id) {
      successful_shared(e, response.post_id);
    }
  });
}


function successful_shared(e, post_id) {
  $.ajax({
    type: 'POST',
    url: e.target.dataset.done,
    data: {
      post: post_id,
      order: e.target.dataset.order,
      hashtag: e.target.dataset.hashtag,
      csrfmiddlewaretoken: e.target.dataset.token},
    success: function (data, status) {
      console.log('Successful!');
      if (e.target.dataset.msgcls) $('.' + e.target.dataset.msgcls).show();
    },
    error: function(jqXHR, status, err) {
      console.log('Error:', err, jqXHR.responseText);
    }
  });
}


function fb_send_ref_link(e) {
  e.preventDefault();
  var msg_txt;

  FB.ui({
    method: 'send',
    link: e.currentTarget.dataset.reflink,
  }, function(response) {
    var $msg = $('.js-invites-msg');
    console.log('response:', response);
    if (response && response.success) {
      msg_txt = gettext('THANK YOU FOR SHARING THE LOVE OF HOOK COFFEE AROUND!');
    } else {
      msg_txt = gettext('Sorry there was an error trying to share invites.');
    }
    $msg.show();
    $msg.html(msg_txt);
    setTimeout(function() {
      $msg.hide();
    }, 5000);
  });
}


function fetch_social_data(apiUrl) {
    $.ajax({
    url: apiUrl,
    success: function(data) {
      handle_fb_reviews(data.fb_reviews, data.fb_overall);
      // handle_insta_posts(data.insta_posts);
    },
  });
}


function handle_fb_reviews(reviews, overall) {
  var $reviewsList = $('.js-fb-reviews'),
      $overallRating = $('.js-fb-overall-rating'),
      $overallRatingCount = $('.js-fb-rating-count'),
      reviewTpl = (
        '<div class="fb-review">' +
          '<div class="fb-review__header">' +
            '<img src="{img}" class="header__profile-pic" />' +
            '<div class="header__user-info">' +
              '<p>' +
                '<b>{name}</b> reviewed ' +
                '<a href="https://www.facebook.com/pg/hookcoffeesg/reviews/?ref=page_internal" class="clr-me-s" target="_blank">Hook Coffee</a> — ' +
                '<span class="fb-rating"><b>{rating}</b> ★</span>' +
              '</p><p><b>{created}</b></p>' +
            '</div>' +
          '</div>' +
          '<div class="fb-review__body">' +
            '<p>{review}</p>' +
          '</div>' +
        '</div>');


  $.each(reviews, function(i, review) {
    var createdAt = moment(review.created_time).format('MMMM DD \\at h:mma'),
        contactHtml = reviewTpl.replace(RegExp('{name}', 'g'), review.reviewer.name)
                                .replace(RegExp('{img}', 'g'), review.img)
                                .replace(RegExp('{rating}', 'g'), review.rating)
                                .replace(RegExp('{created}', 'g'), createdAt)
                                .replace(RegExp('{review}', 'g'), review.review_text);
    $reviewsList.append(contactHtml);
  });
  $overallRating.text(overall.overall_star_rating);
  $overallRatingCount.text(overall.rating_count);
  if (reviews.length > 0) {
    $reviewsList.removeClass('hide');
  }
}


function handle_insta_posts(posts) {
  var $postsList = $('.js-insta-posts'),
      postTpl = (
        '<div class="col-lg-4">' +
          '<div class="social-pc">' +
            '<div class="social-pc-header">' +
              '<div class="avatar">' +
                '<img width="40" height="40" src="{profile_img}" />' +
              '</div>' +
              '<div class="info">' +
                '<p>{full_name}</p>' +
                '<small>{created_time}</small>' +
              '</div>' +
            '</div>' +
            '<div class="social-pc-body">' +
              '<div class="post-image">' +
                '<img src="{img}"/>' +
              '</div>' +
              '<p>{text}</p>' +
            '</div>' +
          '</div>' +
        '</div>');

  $.each(posts, function(i, post) {
    var createdAt = moment(post.created_time, 'X').fromNow(),
        postHtml = postTpl.replace(RegExp('{profile_img}', 'g'), post.profile_img)
                           .replace(RegExp('{full_name}', 'g'), post.full_name)
                           .replace(RegExp('{created_time}', 'g'), createdAt)
                           .replace(RegExp('{img}', 'g'), post.img)
                           .replace(RegExp('{text}', 'g'), post.text);
    $postsList.append(postHtml);
  });
}


$('.js-fb-share').click(fb_share);
$('.js-fb-send-ref-link').click(fb_send_ref_link);

