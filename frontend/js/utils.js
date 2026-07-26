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
  window.MINDHAVEN_CONFIG.API_URL = localStorage.getItem('MINDHAVEN_API_URL') || "https://kritika53245-mindhaven.hf.space/predict";
}
if (!window.MINDHAVEN_CONFIG.GROQ_KEY) {
  window.MINDHAVEN_CONFIG.GROQ_KEY = localStorage.getItem('MINDHAVEN_GROQ_KEY') || "";
}
if (window.MINDHAVEN_CONFIG.NGROK_URL === undefined) {
  window.MINDHAVEN_CONFIG.NGROK_URL = localStorage.getItem('MINDHAVEN_NGROK_URL') || "";
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
  var val = parseFloat(score);
  if (isNaN(val)) return 54;
  
  // Bound to [0.0, 4.0]
  val = Math.max(0.0, Math.min(4.0, val));
  
  // Define anchors
  var anchors = [
    { x: 0.0, y: 92 },
    { x: 1.0, y: 78 },
    { x: 2.0, y: 54 },
    { x: 3.0, y: 32 },
    { x: 4.0, y: 12 }
  ];
  
  // Find segment
  for (var i = 0; i < anchors.length - 1; i++) {
    var a = anchors[i];
    var b = anchors[i+1];
    if (val >= a.x && val <= b.x) {
      var pct = (val - a.x) / (b.x - a.x);
      return Math.round(a.y + pct * (b.y - a.y));
    }
  }
  return 54;
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
  fake = ensureShapData(fake);
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

/* ── SHAP Feature Explanations Metadata & Reconstructor ──────── */
const FEATURE_INFO = [
  { name: "Q1_inv", display_name: "Energy & Vitality", category: "Self-Reported", desc_worsening: "Feeling low on daily energy increased your stress score.", desc_protective: "High daily energy levels helped keep your stress score low." },
  { name: "Q2", display_name: "Focus & Engagement", category: "Self-Reported", desc_worsening: "Feeling unmotivated or disconnected increased your stress score.", desc_protective: "Feeling engaged and motivated helped lower your stress score." },
  { name: "Q3", display_name: "Physical & Mental Exhaustion", category: "Self-Reported", desc_worsening: "Feeling tired and exhausted increased your stress score.", desc_protective: "Feeling rested and calm helped keep your stress score low." },
  { name: "Q4_inv", display_name: "Academic & Personal Progress", category: "Self-Reported", desc_worsening: "Feeling unsatisfied with your progress increased your stress score.", desc_protective: "Feeling proud of your progress helped lower your stress score." },
  { name: "Q5_inv", display_name: "Sense of Accomplishment", category: "Self-Reported", desc_worsening: "Feeling a lack of accomplishment increased your stress score.", desc_protective: "A strong sense of achievement helped reduce your stress score." },
  { name: "Avg_EAR", display_name: "Eye Openness & Focus", category: "Biometrics", desc_worsening: "Tired or heavy eyes indicated physical fatigue, raising your score.", desc_protective: "Alert, open eyes indicated fresh energy, keeping your score low." },
  { name: "Std_EAR", display_name: "Blink Rate & Concentration", category: "Biometrics", desc_worsening: "Irregular blinking patterns suggested eye strain or fatigue.", desc_protective: "Steady, natural blinking patterns indicated calm focus." },
  { name: "Avg_MAR", display_name: "Facial Muscle Tension", category: "Biometrics", desc_worsening: "Jaw tension or yawning suggested physical strain, raising your score.", desc_protective: "Relaxed facial muscles helped lower your stress score." },
  { name: "Std_MAR", display_name: "Facial Expression Changes", category: "Biometrics", desc_worsening: "Frequent facial tension changes suggested physical fatigue.", desc_protective: "Steady, relaxed facial movement suggested ease and calmness." },
  { name: "Positive_Percent", display_name: "Positive Facial Cues", category: "Biometrics", desc_worsening: "Fewer smiles or warm expressions increased your stress score.", desc_protective: "Frequent smiles and warm expressions lowered your stress score." },
  { name: "Neutral_Percent", display_name: "Relaxed Facial Expression", category: "Biometrics", desc_worsening: "Fewer moments of facial relaxation increased your stress score.", desc_protective: "Frequent calm, relaxed facial expressions lowered your score." },
  { name: "Negative_Percent", display_name: "Tension & Concern Marks", category: "Biometrics", desc_worsening: "Expressions of tension or concern increased your stress score.", desc_protective: "Minimal signs of facial worry helped keep your score low." },
  { name: "Sentiment_Pos", display_name: "Voice Positivity", category: "Voice Analysis", desc_worsening: "Fewer positive words in your speech sample increased your score.", desc_protective: "Positive speech sentiment helped lower your stress score." },
  { name: "Sentiment_Neu", display_name: "Voice Calmness", category: "Voice Analysis", desc_worsening: "Lower vocal stability suggested emotional strain while speaking.", desc_protective: "Calm, steady voice delivery helped reduce your score." },
  { name: "Sentiment_Neg", display_name: "Voice Stress Level", category: "Voice Analysis", desc_worsening: "Stress indicators in your speech sample increased your score.", desc_protective: "Absence of stress indicators in your speech kept your score low." },
  { name: "Sentiment_Comp", display_name: "Overall Voice Outlook", category: "Voice Analysis", desc_worsening: "Stressful sentiment in your speech sample increased your score.", desc_protective: "Positive sentiment in your speech sample kept your score low." },
  { name: "Survey_Sum", display_name: "Total Survey Answers", category: "Self-Reported", desc_worsening: "Your overall survey answers were the primary driver of this score.", desc_protective: "Your low survey stress answers helped keep your score low." },
  { name: "Exhaustion_Ratio", display_name: "Facial Fatigue Index", category: "Biometrics", desc_worsening: "Combined facial tension markers indicated physical fatigue.", desc_protective: "Balanced facial markers indicated good physical relaxation." }
];

function ensureShapData(pred) {
  if (!pred) return pred;
  if (pred.shap_contributions && pred.shap_contributions.length > 0) {
    return pred;
  }

  var baseVal = 1.89;
  var score = parseFloat(pred.burnout_score) || 0.0;
  var targetDiff = score - baseVal;

  var debug = pred.debug_data || {};
  var answers = debug["Questionnaire Answers"] || pred.answers || ["Sometimes", "Sometimes", "Sometimes", "Sometimes", "Sometimes"];

  var scoreMap = { "Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4 };
  var q_raw = answers.map(function(ans) { return scoreMap[ans] !== undefined ? scoreMap[ans] : 2; });

  var weights = {};

  var q1_inv = 4 - q_raw[0];
  weights["Q1_inv"] = (2 - q1_inv) * 0.1;
  weights["Q2"] = (q_raw[1] - 2) * 0.1;
  weights["Q3"] = (q_raw[2] - 2) * 0.1;
  var q4_inv = 4 - q_raw[3];
  weights["Q4_inv"] = (2 - q4_inv) * 0.1;
  var q5_inv = 4 - q_raw[4];
  weights["Q5_inv"] = (2 - q5_inv) * 0.1;

  var survey_sum = q1_inv + q_raw[1] + q_raw[2] + q4_inv + q5_inv;
  weights["Survey_Sum"] = (survey_sum - 10) * 0.08;

  var ear = 0.28, mar = 0.15;
  if (debug["EAR"] !== undefined && debug["EAR"] !== null) {
    if (typeof debug["EAR"] === "number") {
      ear = debug["EAR"];
    } else {
      var earMatch = debug["EAR"].toString().match(/([\d.]+)/);
      if (earMatch) ear = parseFloat(earMatch[1]);
    }
  }
  if (debug["MAR"] !== undefined && debug["MAR"] !== null) {
    if (typeof debug["MAR"] === "number") {
      mar = debug["MAR"];
    } else {
      var marMatch = debug["MAR"].toString().match(/([\d.]+)/);
      if (marMatch) mar = parseFloat(marMatch[1]);
    }
  }

  weights["Avg_EAR"] = (0.28 - ear) * 0.5;
  weights["Std_EAR"] = 0.02 * (score > 2 ? 1 : -1);
  weights["Avg_MAR"] = (mar - 0.15) * 0.5;
  weights["Std_MAR"] = 0.02 * (score > 2 ? 1 : -1);
  weights["Exhaustion_Ratio"] = (mar / (ear + 1e-5) - 0.5) * 0.2;

  var pos = 15, neu = 65, neg = 20;
  if (debug["Emotions"]) {
    pos = parseFloat(debug["Emotions"]["Positive %"]) || pos;
    neu = parseFloat(debug["Emotions"]["Neutral %"]) || neu;
    neg = parseFloat(debug["Emotions"]["Negative %"]) || neg;
  }
  weights["Positive_Percent"] = (15 - pos) * 0.005;
  weights["Neutral_Percent"] = (65 - neu) * 0.005;
  weights["Negative_Percent"] = (neg - 20) * 0.008;

  var comp = 0.0;
  if (debug["Sentiment"]) {
    var compMatch = debug["Sentiment"].match(/Comp:\s*([-\d.]+)/);
    if (compMatch) comp = parseFloat(compMatch[1]);
  }
  weights["Sentiment_Pos"] = (comp > 0 ? -0.05 : 0.05);
  weights["Sentiment_Neu"] = -0.02;
  weights["Sentiment_Neg"] = (comp < 0 ? 0.05 : -0.05);
  weights["Sentiment_Comp"] = -comp * 0.15;

  var totalRaw = 0;
  for (var k in weights) {
    totalRaw += weights[k];
  }

  var scale = 1.0;
  if (Math.abs(totalRaw) > 1e-4) {
    scale = targetDiff / totalRaw;
  } else {
    scale = 0;
  }

  var contributions = [];
  FEATURE_INFO.forEach(function(meta) {
    var rawW = weights[meta.name] !== undefined ? weights[meta.name] : 0.0;
    var shapVal = scale === 0 ? (targetDiff / FEATURE_INFO.length) : (rawW * scale);
    if (shapVal > 1.2) shapVal = 1.2;
    if (shapVal < -1.2) shapVal = -1.2;

    var effect = shapVal > 0 ? "worsening" : "protective";
    var desc = shapVal > 0 ? meta.desc_worsening : meta.desc_protective;

    contributions.push({
      name: meta.name,
      display_name: meta.display_name,
      category: meta.category,
      shap_value: shapVal,
      effect: effect,
      description: desc
    });
  });

  var sum = 0;
  contributions.forEach(function(c) { sum += c.shap_value; });
  var adjustment = targetDiff - sum;
  if (contributions.length > 0) {
    contributions[contributions.length - 1].shap_value += adjustment;
  }

  pred.shap_base_value = baseVal;
  pred.shap_contributions = contributions;
  return pred;
}

/* ── Longitudinal Risk Trajectory trend calculator ────────── */
function calculateRiskTrajectory(records) {
  if (!records || records.length === 0) {
    return {
      signal: "Stable",
      delta: 0,
      label: "No Telemetry",
      icon: "trending_flat",
      colorClass: "bg-gray-100 text-gray-700",
      description: "Establish baseline with more assessments."
    };
  }
  
  if (records.length < 2) {
    var r = records[0];
    var score = parseFloat(r.burnout_score) || 0.0;
    return {
      signal: "Stable",
      delta: 0,
      label: "Baseline Created",
      icon: "trending_flat",
      colorClass: "bg-gray-100 text-gray-700",
      description: "Initial score registered: " + score.toFixed(1) + ". Next session determines trend."
    };
  }

  var chronRecords = [...records].sort(function(a, b) {
    return new Date(a.created_at) - new Date(b.created_at);
  });

  var N = chronRecords.length;
  var latest = parseFloat(chronRecords[N - 1].burnout_score) || 0.0;
  var previous = parseFloat(chronRecords[N - 2].burnout_score) || 0.0;
  var delta = latest - previous;
  
  var signal = "Stable";
  var label = "Stable Composure";
  var icon = "trending_flat";
  var colorClass = "bg-yellow-100 text-yellow-700 font-extrabold uppercase tracking-wide";
  var description = "Your stress levels are holding stable. Continue focusing on work-life boundaries.";
  
  if (delta > 0.15) {
    signal = "Rising";
    label = "Rising Stress";
    icon = "trending_up";
    colorClass = "bg-red-100 text-red-700 font-extrabold uppercase tracking-wide";
    description = "Your burnout risk has increased by " + Math.round(delta * 25) + "% since your last session. Rest recommended.";
  } else if (delta < -0.15) {
    signal = "Declining";
    label = "Improving Wellness";
    icon = "trending_down";
    colorClass = "bg-green-100 text-green-700 font-extrabold uppercase tracking-wide";
    description = "Your burnout risk has decreased by " + Math.round(Math.abs(delta) * 25) + "% since your last session. Excellent progress!";
  } else {
    if (latest <= 1.5) {
      colorClass = "bg-green-100 text-green-700 font-extrabold uppercase tracking-wide";
      description = "Your wellness indicators remain consistently positive and stable.";
    } else if (latest >= 3.0) {
      colorClass = "bg-red-100 text-red-700 font-extrabold uppercase tracking-wide";
      description = "Stress indicators remain high and stable. Urgent rest or digital detox is suggested.";
    }
  }

  return {
    signal: signal,
    delta: delta,
    label: label,
    icon: icon,
    colorClass: colorClass,
    description: description
  };
}
