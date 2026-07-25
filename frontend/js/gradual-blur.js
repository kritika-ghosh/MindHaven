/* ═══════════════════════════════════════════════════════════════
   js/gradual-blur.js  —  Vanilla JS port of React Bits <GradualBlur />
   Creates stacked backdrop-filter blur layers with mask-image gradients.
   
   Usage:
     createGradualBlur(containerEl, {
       position: 'bottom',   // 'top' | 'bottom' | 'left' | 'right'
       strength: 2,           // Base blur multiplier
       height: '6rem',        // Height of the blur overlay
       divCount: 5,           // Number of stacked blur layers
       curve: 'bezier',       // 'linear' | 'bezier' | 'ease-in' | 'ease-out'
       exponential: true,     // Use exponential blur progression
       opacity: 1,            // Layer opacity
       zIndex: 50             // z-index of the overlay
     });
     
   Returns: The container div element (for removal if needed)
═══════════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  var CURVE_FUNCTIONS = {
    linear:     function(p) { return p; },
    bezier:     function(p) { return p * p * (3 - 2 * p); },
    'ease-in':  function(p) { return p * p; },
    'ease-out': function(p) { return 1 - Math.pow(1 - p, 2); },
    'ease-in-out': function(p) {
      return p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
    }
  };

  var GRADIENT_DIRECTIONS = {
    top:    'to top',
    bottom: 'to bottom',
    left:   'to left',
    right:  'to right'
  };

  var DEFAULTS = {
    position:    'bottom',
    strength:    2,
    height:      '6rem',
    divCount:    5,
    exponential: false,
    curve:       'linear',
    opacity:     1,
    zIndex:      50
  };

  function mergeOptions(defaults, overrides) {
    var result = {};
    for (var key in defaults) {
      result[key] = defaults[key];
    }
    if (overrides) {
      for (var k in overrides) {
        if (overrides[k] !== undefined) {
          result[k] = overrides[k];
        }
      }
    }
    return result;
  }

  window.createGradualBlur = function(container, options) {
    if (!container) {
      console.warn('createGradualBlur: container element is null');
      return null;
    }

    var config = mergeOptions(DEFAULTS, options);
    var curveFunc = CURVE_FUNCTIONS[config.curve] || CURVE_FUNCTIONS.linear;
    var direction = GRADIENT_DIRECTIONS[config.position] || 'to bottom';
    var isVertical = (config.position === 'top' || config.position === 'bottom');

    // Ensure container is positioned
    var containerStyle = window.getComputedStyle(container);
    if (containerStyle.position === 'static') {
      container.style.position = 'relative';
    }

    // Create the blur wrapper
    var wrapper = document.createElement('div');
    wrapper.className = 'gradual-blur';
    wrapper.style.position = 'absolute';
    wrapper.style.pointerEvents = 'none';
    wrapper.style.zIndex = config.zIndex;

    if (isVertical) {
      wrapper.style.height = config.height;
      wrapper.style.width = '100%';
      wrapper.style.left = '0';
      wrapper.style.right = '0';
      wrapper.style[config.position] = '0';
    } else {
      wrapper.style.width = config.height;
      wrapper.style.height = '100%';
      wrapper.style.top = '0';
      wrapper.style.bottom = '0';
      wrapper.style[config.position] = '0';
    }

    // Inner container
    var inner = document.createElement('div');
    inner.className = 'gradual-blur-inner';
    inner.style.position = 'relative';
    inner.style.width = '100%';
    inner.style.height = '100%';

    // Create blur layers
    var increment = 100 / config.divCount;

    for (var i = 1; i <= config.divCount; i++) {
      var progress = curveFunc(i / config.divCount);
      var blurValue;

      if (config.exponential) {
        blurValue = Math.pow(2, progress * 4) * 0.0625 * config.strength;
      } else {
        blurValue = 0.0625 * (progress * config.divCount + 1) * config.strength;
      }

      var p1 = Math.round((increment * i - increment) * 10) / 10;
      var p2 = Math.round(increment * i * 10) / 10;
      var p3 = Math.round((increment * i + increment) * 10) / 10;
      var p4 = Math.round((increment * i + increment * 2) * 10) / 10;

      var gradient = 'transparent ' + p1 + '%, black ' + p2 + '%';
      if (p3 <= 100) gradient += ', black ' + p3 + '%';
      if (p4 <= 100) gradient += ', transparent ' + p4 + '%';

      var maskVal = 'linear-gradient(' + direction + ', ' + gradient + ')';

      var layer = document.createElement('div');
      layer.style.position = 'absolute';
      layer.style.inset = '0';
      layer.style.maskImage = maskVal;
      layer.style.webkitMaskImage = maskVal;
      layer.style.backdropFilter = 'blur(' + blurValue.toFixed(3) + 'rem)';
      layer.style.webkitBackdropFilter = 'blur(' + blurValue.toFixed(3) + 'rem)';
      layer.style.opacity = config.opacity;

      inner.appendChild(layer);
    }

    wrapper.appendChild(inner);
    container.appendChild(wrapper);

    return wrapper;
  };

})();
