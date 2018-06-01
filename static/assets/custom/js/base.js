$('.js-change-lang').click(change_lang);

function change_lang(e) {
  var lang = e.target.dataset.lang,
      $form = $('form[name="change_lang"]'),
      $full_path = $form.find('input[name="full_path"]').val(),
      $lang_field = $form.find('input[name="language"]'),
      $next_field = $form.find('input[name="next"]'),
      next;
  next = get_next_url($full_path, lang);
  $lang_field.val(lang);
  $next_field.val(next);
  $form.submit();
};


function get_next_url(full_path, new_lang) {
  full_path = full_path.replace('/zh-hans', ''); // remove language prefix
  if (new_lang === 'en') {
    return full_path;
  }
  else {
    return '/' + new_lang + full_path;
  }
}
