step = 18;
credits_to_buy = step * 2;

$(document).ready(function(){
    console.log('js loaded');

    // $("#confirm-credits-modal").modal('show');
    $(".btn-buygift").click(function (evt) {
      var giftType = evt.target.dataset.type;
      var hiddenInput = $("#post_credits");
      var priceTag = $("#buyGift__price");
      var price = '42';

      switch (giftType) {
        case 'gift-lvl2':
          price = '84';
          break;
        case 'gift-lvl3':
          price = '252';
          break;
      };

      hiddenInput.val(Number(price));
      priceTag.text('S$' + price);

      $('#credits_amount').val(price);
      $("#number").val(price + '$');
    });

    $("#submit-credits-buy").on('click', function(){
        var form = $('#payment-form');
        // $('#payment-form').submit();

        if ($("[name=recipient_name]").val().length === 0 ) {
          $("[name=recipient_name]").css("border", "1px solid red");
            return false;
        } else {
          $("[name=recipient_name]").css("border", "");
        }

        if ($("[name=email]").val().length === 0 ) {
          $("[name=email]").css("border", "1px solid red");
            return false;
        } else {
          $("[name=email]").css("border", "");
        }

    });

    $('.menu-icon').click(function(){
        var hidden = $('.hemburger-menu');
        if (hidden.hasClass('visible')){
            hidden.animate({"left":"-300px"}, "slow").removeClass('visible');
        } else {
            hidden.animate({"left":"0px"}, "slow").addClass('visible');
        }
    });

    /*
    $(function() {
        $( "#slider-range-min" ).slider({
          range: "min",
          value: step * 2,
          min: 18,
          max: 360,
          step: 18,
          slide: function( event, ui ) {
            $( "#amount" ).val( "$" + ui.value );
            credits_to_buy = Number(ui.value);
            $('#credits_amount').val(credits_to_buy);
            $('#post_credits').val(credits_to_buy);
            $("#number").val(credits_to_buy +'$');
            $("#amount-to-pay").html(credits_to_buy);
        }
    });
        $( "#amount" ).val( "$" + $( "#slider-range-min" ).slider( "value" ) );
    });
*/
    $("#increment-x").click(function(){
        if($('#credits_amount').val() < step * 20){
            credits_to_buy = Number($('#credits_amount').val()) + step;
            $('#post_credits').val(credits_to_buy);
            $('#credits_amount').val(credits_to_buy);
            $("#number").val(credits_to_buy +'$');
            $("#amount-to-pay").html(credits_to_buy);
        }
    });

    $("#decrement-x").click(function(){
        if($('#credits_amount').val() > step){
            credits_to_buy = Number($('#credits_amount').val()) - step;
            $('#post_credits').val(credits_to_buy);
            $('#credits_amount').val(credits_to_buy);
            $("#number").val(credits_to_buy + '$');
            $("#amount-to-pay").html(credits_to_buy);
        }
    });
});
