/* ═══════════════════════════════════════════════════════════════
   js/utils.js  —  Shared helpers used across all pages
═══════════════════════════════════════════════════════════════ */

/* ── Page transition (fade to dark, then navigate) ──────────── */
function navigateTo(href) {
  var overlay = document.getElementById('page-transition-overlay');
  if (!overlay) { window.location.href = href; return; }
  overlay.style.pointerEvents = 'all';
  overlay.style.opacity = '1';
  setTimeout(function () { window.location.href = href; }, 520);
}

/* ── Entrance animation (GSAP if available, CSS fallback) ───── */
function pageEntrance(selector, opts) {
  var el = document.querySelector(selector);
  if (!el) return;
  opts = opts || {};
  if (typeof gsap !== 'undefined') {
    gsap.from(el, {
      duration: opts.duration || 0.65,
      opacity:  0,
      y:        opts.y   !== undefined ? opts.y   : 18,
      ease:     opts.ease || 'power2.out',
      delay:    opts.delay || 0,
    });
  } else {
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    el.style.opacity    = '0';
    el.style.transform  = 'translateY(18px)';
    requestAnimationFrame(function () {
      el.style.opacity   = '1';
      el.style.transform = 'translateY(0)';
    });
  }
}

/* ── Staggered children entrance ────────────────────────────── */
function staggerEntrance(parentSelector, childSelector, delay) {
  delay = delay || 0.12;
  if (typeof gsap === 'undefined') return;
  gsap.from(parentSelector + ' ' + childSelector, {
    scrollTrigger: { trigger: parentSelector, start: 'top 82%' },
    y: 20, opacity: 0,
    duration: 0.55,
    ease: 'power2.out',
    stagger: delay,
  });
}

/* ── Vitality score from burnout score ──────────────────────── */
function burnoutToVitality(score) {
  var map = { 0: 92, 1: 78, 2: 54, 3: 32, 4: 12 };
  return map[Math.round(score)] || 54;
}

/* ── Burnout label from score ───────────────────────────────── */
function burnoutLabel(score) {
  var labels = ['Low', 'Mild', 'Moderate', 'High', 'Severe'];
  return labels[Math.round(score)] || 'Moderate';
}

/* ── Load prediction from localStorage ─────────────────────── */
function loadPrediction() {
  try {
    var raw = localStorage.getItem('burnout_prediction');
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

/* ── Seed fake demo data for guest / judge login ────────────── */
function seedGuestData() {
  var fake = {
    burnout_score: 2,
    suggestion: 'Based on your multi-modal biometric profile, you are experiencing Moderate Burnout. Your facial expression analysis detected elevated brow tension (EAR: 0.24) and reduced smile frequency. Speech sentiment analysis revealed a compound negativity score of -0.18 with a slightly monotone vocal pitch pattern. Recommended interventions: 20-min daily mindfulness sessions, strict work-hour boundaries, and periodic Nadi Shodhana pranayama.',
    debug_data: {
      'Questionnaire Answers': ['Rarely', 'Often', 'Sometimes', 'Often', 'Sometimes'],
      'EAR': '0.24 \u00b1 0.04',
      'MAR': '0.18 \u00b1 0.03',
      'Emotions': { 'Positive %': '8%', 'Neutral %': '57%', 'Negative %': '35%' },
      'Voice Transcript': "I've been pretty stressed lately... work deadlines are piling up and I can't seem to switch off even in the evenings.",
      'Sentiment': 'Pos: 0.06, Neu: 0.62, Neg: 0.32, Comp: -0.18',
      'Pitch': '118 Hz avg (slightly low)',
    },
  };
  localStorage.setItem('mindhaven_guest', 'true');
  localStorage.setItem('mindhaven_auth', 'true');
  localStorage.setItem('mindhaven_user', 'Judge (Demo)');
  localStorage.setItem('burnout_prediction', JSON.stringify(fake));
}

/* ── Auth guard ─────────────────────────────────────────────── */
function requireAuth(redirectTo) {
  redirectTo = redirectTo || 'auth.html';
  var isAuth  = localStorage.getItem('mindhaven_auth')  === 'true';
  var isGuest = localStorage.getItem('mindhaven_guest') === 'true';
  if (!isAuth && !isGuest) {
    window.location.href = redirectTo;
    return false;
  }
  return true;
}
