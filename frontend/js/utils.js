/* ── Supabase Initialization ───────────────────────────────── */
const SUPABASE_URL = "https://dunaajtllzvwqguvuebg.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_camf03NTjQHIr5pK-V1DDA_fr8nzNcK";
let sb = null;

if (typeof supabase !== 'undefined') {
  sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: {
      storage: window.sessionStorage,
      persistSession: true
    }
  });
} else {
  console.warn("Supabase SDK is not loaded. Please include the SDK script before utils.js.");
}

/* ── Configuration Defaults & Overrides ───────────────────── */
window.MINDHAVEN_CONFIG = window.MINDHAVEN_CONFIG || {};
if (!window.MINDHAVEN_CONFIG.API_URL) {
  window.MINDHAVEN_CONFIG.API_URL = "https://kritika53245-mindhaven.hf.space/predict";
}
if (!window.MINDHAVEN_CONFIG.GROQ_KEY) {
  window.MINDHAVEN_CONFIG.GROQ_KEY = "";
}

/* ═══════════════════════════════════════════════════════════════
   js/utils.js  —  Shared helpers used across all pages
   Customized for Supabase & Burnout Assessment
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

/* ── Load prediction from sessionStorage ─────────────────────── */
function loadPrediction() {
  try {
    var raw = sessionStorage.getItem('burnout_prediction');
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
  sessionStorage.setItem('mindhaven_guest', 'true');
  sessionStorage.setItem('mindhaven_auth', 'true');
  sessionStorage.setItem('mindhaven_user', 'Judge (Demo)');
  sessionStorage.setItem('burnout_prediction', JSON.stringify(fake));
}

/* ── Auth guard ─────────────────────────────────────────────── */
async function requireAuth(redirectTo) {
  redirectTo = redirectTo || 'auth.html';
  var isGuest = sessionStorage.getItem('mindhaven_guest') === 'true';
  if (isGuest) {
    return { user: { email: 'guest@mindhaven.demo', user_metadata: { full_name: 'Judge (Demo)' } } };
  }
  
  if (sb) {
    try {
      const { data: { session } } = await sb.auth.getSession();
      if (session) {
        sessionStorage.setItem('mindhaven_auth', 'true');
        sessionStorage.setItem('mindhaven_user', session.user.user_metadata?.full_name || session.user.email || 'User');
        return session;
      }
    } catch (e) {
      console.error("Supabase session check failed:", e);
    }
  }
  
  window.location.href = redirectTo;
  return null;
}

/* ── Save assessment results to Supabase ────────────────────── */
async function saveAssessment(predictionData, answers) {
  if (!sb) {
    console.warn('Supabase is not initialized. Skipping DB save.');
    return null;
  }
  
  try {
    const { data: { session } } = await sb.auth.getSession();
    if (!session) {
      console.log('User is guest or not logged in. Skipping DB save.');
      return null;
    }
    
    var debug = predictionData.debug_data || {};
    var emotions = debug['Emotions'] || {};
    
    // Extract compound sentiment score
    var sentimentStr = debug['Sentiment'] || '';
    var compoundScore = null;
    if (sentimentStr) {
      var match = sentimentStr.match(/Comp:\s*([-\d.]+)/i);
      if (match) compoundScore = parseFloat(match[1]);
    }
    
    // Helper to clean numeric values
    var parseVal = function(v) {
      if (!v) return null;
      var clean = parseFloat(v.toString().replace(/%/g, ''));
      return isNaN(clean) ? null : clean;
    };
    
    var row = {
      user_id: session.user.id,
      answers: answers,
      burnout_score: parseFloat(predictionData.burnout_score),
      vitality_score: burnoutToVitality(predictionData.burnout_score),
      suggestion: predictionData.suggestion,
      ear: parseVal(debug['EAR']),
      mar: parseVal(debug['MAR']),
      emo_pos: parseVal(emotions['Positive %']),
      emo_neu: parseVal(emotions['Neutral %']),
      emo_neg: parseVal(emotions['Negative %']),
      sentiment_compound: compoundScore,
      voice_transcript: debug['Voice Transcript'] || null,
      llm_insight: predictionData.llm_insight || null
    };
    
    const { data, error } = await sb.from('assessments').insert(row).select();
    if (error) {
      console.error('Error inserting assessment:', error.message);
      return null;
    }
    console.log('Successfully saved assessment to Supabase:', data);
    return data;
  } catch (err) {
    console.error('Failed to save assessment:', err);
    return null;
  }
}
