$(window).load(function() {
// carousel is the images that you can scroll through
  initializeCarousels();
  ScoringImages.init();
  ScoringKeyboardShortcuts.init();
  addScoringKeyboardShortcutsModalListener();
});


const KEYS = {
  UP: 38,
  DOWN: 40,
  SLASH: 191,
  ZERO: 48,
  NINE: 57,
  ZERO_NUMPAD: 96,
  NINE_NUMPAD: 105,
};


function initializeCarousels() {
  var carousels = $(".carousel");
  if (!carousels.length) {
    return;
  }

  carousels.each(function() {
    var el = $(this);
    var firstImage = el.find(".individual-image").first();
    addImageElement(firstImage);
    firstImage.addClass("show");
  });

  carousels.find(".image-frame-navigation").click(function(e) {
    e.preventDefault();
    var navigator = $(this);
    var carousel = navigator.closest(".carousel");

    var direction;
    if (navigator.hasClass("image-frame-previous")) {
      direction = "previous";
    } else {
      direction = "next";
    }

    showSubsequentImage(carousel, direction);
  });
};


function showSubsequentImage(carousel, direction) {
  var images = carousel.find(".individual-image");
  var currentImage = carousel.find(".show");
  var i = images.index(currentImage);
  images.eq(i).removeClass("show");

  if (direction === "next") {
    i = (++i) % images.length;
  } else {
    i = (--i) % images.length;
  }

  var subsequentImage = images.eq(i);
  subsequentImage.addClass("show");
  addImageElement(subsequentImage);
};


function addImageElement(image) {
  var imageFrame = image.find(".image-frame");
  var imageSrc = imageFrame.attr("data-src");
  imageFrame.prepend("<img src='" + imageSrc + "' \>");
};


var ScoringImages = {
  init: function() {
    this.imageFrames = $(".image-frame");
    this.imageFrameIndex = 0;
    this.loadImages();
  },

  loadImages: function() {
    var imageFrames = $(this.imageFrames);
    imageFrames.each(function() {
      var imageFrame = $(this);
      var imageSrc = imageFrame.attr("data-src");
      var image = $("<img>");

      image.attr("src", imageSrc).load(function() {
        imageFrame.removeClass("loading");
        imageFrame.prepend(image);
      });
    });
  },
};


var ScoringKeyboardShortcuts = {
  init: function() {
    if (!$("#score-experiment-wells").length) {
      return;
    }

    this.experiments = $(".experiment");
    if (!this.experiments.length) {
      return;
    }

    this.currentExperimentIndex = 0;
    this.activateExperiment();
    this.listen();
  },

  listen: function() {
    $("body").on("keydown", function(e) {
      ScoringKeyboardShortcuts.handleKeyboardShortcut(e);
    });
  },

  handleKeyboardShortcut: function(e) {
    switch(e.which) {
      case KEYS.UP:
        e.preventDefault();

        if (e.shiftKey) {
          this.navigateKeyableGroups(KEYS.UP);
        } else {
          this.navigateExperiments(KEYS.UP);
        }

        break;

      case KEYS.DOWN:
        e.preventDefault();

        if (e.shiftKey) {
          this.navigateKeyableGroups(KEYS.DOWN);
        } else {
          this.navigateExperiments(KEYS.DOWN);
        }

        break;

      default:
        if (this.isDigitKey(e.which)) {
          e.preventDefault();

          var key = this.getDigitKey(e.which);

          if (!e.shiftKey) {
            this.score(key);
          } else {
            this.score(key + 10);
          }
        }
    }
  },

  score: function(keyIndex) {
    var group = this.getKeyableGroup();
    var input = $(group.find(".keyable")[keyIndex]);

    // Do not proceed if keyIndex greater than number of keys
    if (!input.length) {
      return;
    }

    input.trigger("click");
    this.navigateKeyableGroups(KEYS.DOWN);
  },

  navigateExperiments: function(direction) {
    var nextIndex;
    if (direction === KEYS.UP) {
      nextIndex = this.currentExperimentIndex - 1;
    } else if (direction === KEYS.DOWN) {
      nextIndex = this.currentExperimentIndex + 1;
    }

    var submitButton = $(".submit");
    submitButton.blur();

    // If past the last experiment, move down to show and focus Submit button
    if (nextIndex < 0 || nextIndex > this.experiments.length) {
      return;
    }

    this.currentExperimentIndex = nextIndex;

    if (nextIndex === this.experiments.length) {
      $("html, body").scrollTop($("body").height());
      submitButton.focus();
    } else {
      this.activateExperiment();
    }
  },

  navigateKeyableGroups: function(direction) {
    var nextIndex;
    if (direction === KEYS.UP) {
      nextIndex = this.keyableGroupIndex - 1;
    } else if (direction === KEYS.DOWN) {
      nextIndex = this.keyableGroupIndex + 1;
    }

    if (nextIndex < 0 || nextIndex >= this.keyableGroups.length) {
      return;
    }

    this.keyableGroupIndex = nextIndex;
    this.activateKeyableGroup();
  },

  activateExperiment: function() {
    $(this.experiments).removeClass("active");
    var experiment = $(this.experiments[this.currentExperimentIndex]);
    experiment.addClass("active");
    this.initializeKeyableGroups(experiment);
    this.activateKeyableGroup();
    $("html, body").scrollTop(experiment.position().top);
  },

  activateKeyableGroup: function() {
    $(".active-keyable-group").removeClass("active-keyable-group");
    var group = this.getKeyableGroup();
    group.addClass("active-keyable-group");
  },

  initializeKeyableGroups: function(experiment) {
    var buttons = experiment.find(".keyable");
    var groups = [];

    buttons.each(function() {
      var id = $(this).closest("ul").attr("id");

      if (id != groups[groups.length - 1]) {
        groups.push(id);
      }
    });

    this.keyableGroups = groups;
    this.keyableGroupIndex = 0;
  },

  getKeyableGroup: function() {
    return $("#" + this.keyableGroups[this.keyableGroupIndex]);
  },

  isDigitKey: function(code) {
    // Two cases: lower range covers numbers above QWERTY; other is numpad
    return (code >= KEYS.ZERO && code <= KEYS.NINE) ||
           (code >= KEYS.ZERO_NUMPAD && code <= KEYS.NINE_NUMPAD);
  },

  getDigitKey: function(code) {
    if (code >= KEYS.ZERO && code <= KEYS.NINE) {
      return code - KEYS.ZERO;
    } else if (code >= KEYS.ZERO_NUMPAD && code <= KEYS.NINE_NUMPAD) {
      return code - KEYS.ZERO_NUMPAD;
    }
  },
};


function addScoringKeyboardShortcutsModalListener() {
  $("body").on("keyup", function(e) {
    if (e.which == KEYS.SLASH && e.shiftKey) {
      $("#keyboard-shortcuts-modal").toggleClass("visible");
    }
  });
}
