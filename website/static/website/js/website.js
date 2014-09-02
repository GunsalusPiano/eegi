$(document).ready(function() {
  removePageTitleStyleIfEmpty();
  setResizeHandler();
  positionFooter();
})

removePageTitleStyleIfEmpty = function() {
  pageTitle = $("#page-title");
  if (pageTitle.is(":empty")) {
    pageTitle.remove();
  }
}

setResizeHandler = function() {
  $(window).resize(function() {
    positionFooter();
  })
}

positionFooter = function() {
  footer = $("#footer");
  footerHeight = footer.outerHeight();
  footerWidth= footer.width();
  windowHeight = $(window).height();
  contentHeight = $("html").height();

  // if footer is absolute, it is not included in the content height, so add it
  if (footer.css("position") == "absolute") {
    contentHeight += footerHeight;
  }

  // if content is smaller than window, position the footer at bottom of page
  // otherwise position it statically (necessary in case user resizes window)
  footer.css(
    (contentHeight < windowHeight) ? {
      position: "absolute",
      bottom: parseInt($("body").css("paddingBottom"), 10),
      left: parseInt($("body").css("paddingLeft"), 10),
      width: footerWidth
    } : {
      position: "static"
    }
  )
}