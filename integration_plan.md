# MindHaven — Full-Stack Integration Plan

**Goal:** Wire real authentication, persistent burnout history, and LLM-generated insights into the existing HTML/JS frontend without changing the tech stack (no React, no build step).

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    STATIC FRONTEND (Vercel / any host)           │
│                                                                  │
│  auth.html ──► assess.html ──► insights.html ──► dashboard.html  │
│       │              │               │                  │        │
│   Supabase        HF Space        Groq API          Supabase    │
│     Auth          /predict        (LLM)              SELECT      │
└──────────────────────────────────────────────────────────────────┘
         │                                                  │
    ┌────▼────────────────────────────────────────────┐    │
    │              SUPABASE (Free Tier)               │    │
    │                                                 │◄───┘
    │  auth.users  (managed by Supabase Auth)         │
    │  assessments (scores, answers, facial, voice)   │
    └─────────────────────────────────────────────────┘
```

---

## Part 1 — Authentication with Supabase

### Why Supabase?
- Free tier: 500MB DB, 50k monthly active users, built-in Auth UI
- Generates a REST API automatically — works with plain `fetch()`, no SDK required (though the JS SDK is tiny and CDN-available)
- Supports Email/Password + Google OAuth out of the box

### Step 1.1 — Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Note down:
   - **Project URL**: `https://xxxx.supabase.co`
   - **Anon/Public Key**: a long JWT string (safe to expose in frontend)
3. In **Authentication → Settings → Email**, enable "Confirm email" or disable it for hackathon speed

### Step 1.2 — Add Supabase JS SDK to every HTML page

```html
<!-- Add to <head> of auth.html, assess.html, insights.html -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
  const SUPABASE_URL = 'https://YOUR-PROJECT.supabase.co';
  const SUPABASE_KEY = 'YOUR-ANON-KEY';
  const sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
</script>
```

### Step 1.3 — Replace fake auth in `auth.html`

Replace the current `handleAuthSubmit()` with:

```js
// Sign In
async function handleSignIn(email, password) {
  const { data, error } = await sb.auth.signInWithPassword({ email, password });
  if (error) { showError(error.message); return; }
  // Supabase stores the session in localStorage automatically
  window.location.href = 'assess.html';
}

// Sign Up
async function handleSignUp(name, email, password) {
  const { data, error } = await sb.auth.signUp({
    email, password,
    options: { data: { full_name: name } }
  });
  if (error) { showError(error.message); return; }
  window.location.href = 'assess.html';
}

// Google OAuth (one-click)
async function googleLogin() {
  await sb.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: window.location.origin + '/assess.html' }
  });
}

// Guest login — still works, just flags the session
function guestLogin() {
  localStorage.setItem('mindhaven_guest', 'true');
  seedFakeData();
  window.location.href = 'insights.html';
}
```

### Step 1.4 — Auth Guard on protected pages

Replace `localStorage.getItem('mindhaven_auth')` checks with:

```js
// At the top of assess.html, insights.html, dashboard.html
async function requireAuth() {
  const { data: { session } } = await sb.auth.getSession();
  const isGuest = localStorage.getItem('mindhaven_guest') === 'true';
  if (!session && !isGuest) {
    window.location.href = 'auth.html';
    return null;
  }
  return session;
}
```

---

## Part 2 — Supabase Database Schema

### Step 2.1 — Run this SQL in Supabase → SQL Editor

```sql
-- Assessment results table
create table public.assessments (
  id          uuid        default gen_random_uuid() primary key,
  user_id     uuid        references auth.users on delete cascade,
  created_at  timestamptz default now(),

  -- Questionnaire
  answers     jsonb       not null,   -- ["Never","Often","Sometimes","Often","Rarely"]
  
  -- Model output
  burnout_score  float    not null,   -- 0.0 – 4.0
  vitality_score int      not null,   -- 0 – 100 (derived)
  suggestion     text,                -- raw text from HF model
  
  -- Facial biometrics
  ear         float,                  -- Eye Aspect Ratio avg
  mar         float,                  -- Mouth Aspect Ratio avg
  emo_pos     float,                  -- positive emotion %
  emo_neu     float,                  -- neutral emotion %
  emo_neg     float,                  -- negative emotion %

  -- Voice
  sentiment_compound float,
  voice_transcript   text,

  -- LLM
  llm_insight text                    -- Groq-generated personalised analysis
);

-- Row-Level Security: users can only read/write their own rows
alter table public.assessments enable row level security;

create policy "Users see own assessments"
  on public.assessments for select
  using (auth.uid() = user_id);

create policy "Users insert own assessments"
  on public.assessments for insert
  with check (auth.uid() = user_id);
```

### Step 2.2 — Save an assessment from `assess.html`

After the `/predict` API returns, call:

```js
async function saveAssessment(predictionData, answers) {
  const { data: { session } } = await sb.auth.getSession();
  if (!session) return; // skip for guests

  const debug = predictionData.debug_data || {};
  const emotions = debug['Emotions'] || {};

  const row = {
    user_id:       session.user.id,
    answers:       answers,                              // array of 5 strings
    burnout_score: predictionData.burnout_score,
    vitality_score: computeVitality(predictionData.burnout_score),
    suggestion:    predictionData.suggestion,
    ear:           parseFloat(debug['EAR']) || null,
    mar:           parseFloat(debug['MAR']) || null,
    emo_pos:       parseFloat(emotions['Positive %']) || null,
    emo_neu:       parseFloat(emotions['Neutral %'])  || null,
    emo_neg:       parseFloat(emotions['Negative %']) || null,
    sentiment_compound: extractCompound(debug['Sentiment']),
    voice_transcript:   debug['Voice Transcript'] || null,
    llm_insight:   null  // filled after Groq call (see Part 3)
  };

  const { error } = await sb.from('assessments').insert(row);
  if (error) console.error('Save failed:', error.message);
}
```

---

## Part 3 — LLM Integration with Groq

### Why Groq?
- **Free tier**: generous rate limits, no credit card needed
- **Speed**: 500+ tokens/sec (vs OpenAI's ~60)
- **Models**: `llama3-70b-8192`, `mixtral-8x7b-32768`
- **OpenAI-compatible API**: works with standard `fetch()`

### Step 3.1 — Get a Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Create account → **API Keys → Create Key**
3. Store the key — it looks like `gsk_xxxxxxxxxxxx`

> **Security Note for Hackathon**: For a hackathon demo, putting the key in frontend JS is acceptable. For production, proxy through a Supabase Edge Function (covered in Step 3.3).

### Step 3.2 — Call Groq from `insights.html`

```js
const GROQ_KEY   = 'gsk_YOUR_GROQ_KEY_HERE';
const GROQ_MODEL = 'llama3-70b-8192';

async function generateLLMInsight(predictionData, answers) {
  const debug = predictionData.debug_data || {};
  const scoreLabels = ['Low', 'Mild', 'Moderate', 'High', 'Severe'];
  const label = scoreLabels[Math.round(predictionData.burnout_score)] || 'Moderate';

  const prompt = `
You are MindHaven, an empathetic AI wellness coach. Analyse the following burnout assessment data and provide a warm, personalised, actionable mental health report in 3 short paragraphs (no bullet points, no headers). Be specific — reference the actual numbers.

ASSESSMENT DATA:
- Burnout Score: ${predictionData.burnout_score}/4.0 (${label})
- Questionnaire Answers (5 questions on frequency of burnout symptoms):
  Q1 (Mental clarity): ${answers[0]}
  Q2 (Disconnecting from work): ${answers[1]}
  Q3 (Physical/emotional drain): ${answers[2]}
  Q4 (Lack of motivation): ${answers[3]}
  Q5 (Irritability): ${answers[4]}
- Facial Analysis: Eye tension (EAR): ${debug['EAR'] || 'N/A'}, Mouth tension (MAR): ${debug['MAR'] || 'N/A'}
- Emotional Expression: Positive ${debug['Emotions']?.['Positive %'] || '?'}, Neutral ${debug['Emotions']?.['Neutral %'] || '?'}, Negative ${debug['Emotions']?.['Negative %'] || '?'}
- Voice Transcript: "${debug['Voice Transcript'] || 'Not captured'}"
- Voice Sentiment: ${debug['Sentiment'] || 'N/A'}

Paragraph 1: What the data reveals about this person's current mental state (empathetic, non-clinical tone).
Paragraph 2: The most important immediate action they should take today.
Paragraph 3: A 7-day recovery micro-plan with 3 specific, time-bound actions.
`.trim();

  const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + GROQ_KEY
    },
    body: JSON.stringify({
      model: GROQ_MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 600,
      temperature: 0.7
    })
  });

  const json = await res.json();
  return json.choices?.[0]?.message?.content || predictionData.suggestion;
}
```

### Step 3.3 — (Production) Secure the key via Supabase Edge Function

Instead of exposing the Groq key in frontend JS, create a Supabase Edge Function:

```
supabase/functions/generate-insight/index.ts
```

```typescript
import { serve } from 'https://deno.land/std/http/server.ts'

serve(async (req) => {
  const { assessmentData, answers } = await req.json()
  
  // Groq key is a secret env var — never visible to client
  const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('GROQ_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ model: 'llama3-70b-8192', messages: [...], max_tokens: 600 })
  })
  
  const data = await res.json()
  return new Response(JSON.stringify({ insight: data.choices[0].message.content }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
```

Then from the frontend: `await sb.functions.invoke('generate-insight', { body: { assessmentData, answers } })`

---

## Part 4 — Dashboard (Burnout Patterns)

### Step 4.1 — Create `dashboard.html`

A new page with:
- **Trend line chart** — vitality score over time (last 10 assessments)
- **Average burnout score** — this week vs last week
- **Emotion heatmap** — pos/neu/neg over dates
- **Most common answers** — what questions score highest

### Step 4.2 — Fetch history from Supabase

```js
async function loadHistory() {
  const { data, error } = await sb
    .from('assessments')
    .select('created_at, burnout_score, vitality_score, emo_pos, emo_neu, emo_neg, answers')
    .order('created_at', { ascending: false })
    .limit(30);

  if (error) { console.error(error); return; }
  renderCharts(data);
}
```

### Step 4.3 — Charts with Chart.js (CDN, no install)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

```js
function renderCharts(rows) {
  const labels  = rows.map(r => new Date(r.created_at).toLocaleDateString());
  const scores  = rows.map(r => r.vitality_score);

  new Chart(document.getElementById('trend-chart'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Vitality Score',
        data: scores,
        borderColor: '#6b38d4',
        backgroundColor: 'rgba(107,56,212,0.08)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#8455ef',
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { min: 0, max: 100 } }
    }
  });
}
```

---

## Part 5 — Deployment on Vercel

Since the frontend is pure HTML/JS, deploying to Vercel takes 2 minutes:

```bash
# Option A: Vercel CLI
npm i -g vercel
cd frontend/
vercel --prod   # follow prompts, done

# Option B: Vercel Dashboard
# Drag the /frontend folder to vercel.com/new
```

**Environment variables to set in Vercel dashboard:**
| Variable | Value |
|---|---|
| Not needed | Keys go in HTML for hackathon; use Edge Functions for prod |

---

## Implementation Order (Recommended)

```
Week/Day  Task
────────────────────────────────────────────────────────
Day 1     Set up Supabase project + run SQL schema
          Integrate Supabase SDK in auth.html
          Replace localStorage auth with sb.auth.signIn/Up

Day 2     Wire saveAssessment() after /predict call
          Get Groq API key
          Add generateLLMInsight() to insights.html
          Replace static "diagnosis-text" with LLM output

Day 3     Build dashboard.html with Chart.js trend charts
          Load real assessment history from Supabase
          Add Google OAuth button to auth.html

Day 4     (Optional) Move Groq key to Supabase Edge Function
          Deploy frontend to Vercel
          Test end-to-end as a real user
```

---

## Quick Reference — Key API Calls

| What | Code |
|---|---|
| Sign up | `sb.auth.signUp({ email, password })` |
| Sign in | `sb.auth.signInWithPassword({ email, password })` |
| Get session | `sb.auth.getSession()` |
| Sign out | `sb.auth.signOut()` |
| Insert row | `sb.from('assessments').insert(row)` |
| Fetch history | `sb.from('assessments').select('*').order('created_at')` |
| Groq chat | `fetch('https://api.groq.com/openai/v1/chat/completions', ...)` |

---

## Cost Summary (All Free for Hackathon)

| Service | Free Tier |
|---|---|
| **Supabase** | 500MB DB, 50k MAU, 2 projects |
| **Groq** | ~14k tokens/min free (ample for demo) |
| **Vercel** | Unlimited static deploys |
| **Hugging Face Spaces** | Already running (your model) |

**Total monthly cost for hackathon demo: $0**
