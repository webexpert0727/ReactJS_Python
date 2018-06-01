$(document).ready(function(){
    $(".endless_more").text("");
    $(".endless_more").append("<h3 class=''>Load more...</h3>");
    $(".endless_more").on("click", function(){
        $.endlessPaginate({
            paginateOnScroll: true,
            paginateOnScrollMargin: 200,
            paginateOnScrollChunkSize: 5,
          });
    });
})
