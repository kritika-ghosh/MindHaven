/* ═══════════════════════════════════════════════════════════════
   js/theme.js  —  Shared Tailwind config + Theme Toggle
   Include this BEFORE other scripts on every page.
   Handles: system preference detection, localStorage persistence,
   toggle function, and Tailwind config.
═══════════════════════════════════════════════════════════════ */

/* ── Theme Initialization (runs immediately to prevent flash) ── */
(function initTheme() {
  var saved = localStorage.getItem('mindhaven_theme');
  var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var theme = saved || (prefersDark ? 'dark' : 'light');

  document.documentElement.classList.remove('dark', 'light');
  document.documentElement.classList.add(theme);

  // Update meta theme-color for mobile browsers
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content', theme === 'dark' ? '#120F17' : '#faf9fc');
  }
})();

/* ── Toggle Function (exposed globally for onclick) ────────── */
window.toggleTheme = function() {
  var html = document.documentElement;
  var isDark = html.classList.contains('dark');
  var newTheme = isDark ? 'light' : 'dark';

  html.classList.remove('dark', 'light');
  html.classList.add(newTheme);
  localStorage.setItem('mindhaven_theme', newTheme);

  // Update meta theme-color
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content', newTheme === 'dark' ? '#120F17' : '#faf9fc');
  }

  // Dispatch custom event for components that need to react
  window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: newTheme } }));
};

/* ── Tailwind Configuration ────────────────────────────────── */
(function () {
  if (typeof tailwind === 'undefined') return;

  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          'primary':                  'var(--col-primary)',
          'secondary':                'var(--col-secondary)',
          'tertiary':                 '#5d5a69',
          'background':               'var(--col-bg-deep)',
          'surface':                  'var(--col-bg-surface)',
          'surface-bright':           'var(--col-bg-surface)',
          'surface-dim':              'var(--col-bg-elevated)',
          'surface-container':        'var(--col-bg-elevated)',
          'surface-container-low':    'var(--col-bg-surface)',
          'surface-container-high':   'var(--col-bg-hover)',
          'surface-container-highest':'var(--col-bg-hover)',
          'surface-container-lowest': 'var(--col-bg-surface)',
          'on-surface':               'var(--col-text-primary)',
          'on-surface-variant':       'var(--col-text-secondary)',
          'on-background':            'var(--col-text-primary)',
          'on-primary':               '#ffffff',
          'on-secondary':             '#ffffff',
          'on-tertiary':              '#ffffff',
          'primary-container':        'var(--col-primary-glow)',
          'secondary-container':      'var(--col-secondary)',
          'primary-fixed':            '#e9ddff',
          'primary-fixed-dim':        '#d0bcff',
          'secondary-fixed':          '#ebdcff',
          'secondary-fixed-dim':      '#d3bbff',
          'inverse-primary':          '#d0bcff',
          'inverse-surface':          '#313030',
          'inverse-on-surface':       '#f3f0ef',
          'outline':                  'var(--col-text-tertiary)',
          'outline-variant':          'var(--col-border)',
          'surface-tint':             'var(--col-primary)',
          'error':                    'var(--col-danger)',
          'on-error':                 '#ffffff',
          'error-container':          '#ffdad6',
          'on-error-container':       '#93000a',
        },
        borderRadius: {
          DEFAULT: '0.25rem', lg: '0.5rem', xl: '0.75rem', full: '9999px',
        },
        spacing: {
          'margin-mobile':  '20px',
          'margin-desktop': '64px',
          'container-max':  '1280px',
          'gutter':         '24px',
        },
        fontFamily: {
          'body-md':  ['Inter', 'Plus Jakarta Sans', 'sans-serif'],
          'title-md': ['Plus Jakarta Sans', 'sans-serif'],
        },
      },
    },
  };
})();

/* ── Global Logout Helper ─────────────────────────────────── */
window.handleLogout = async function() {
  sessionStorage.removeItem('mindhaven_auth');
  sessionStorage.removeItem('mindhaven_guest');
  sessionStorage.removeItem('mindhaven_user');
  sessionStorage.removeItem('burnout_prediction');
  
  if (window.sb) {
    await window.sb.auth.signOut().catch(function() {});
  }
  
  if (typeof navigateTo === 'function') {
    navigateTo('auth.html');
  } else {
    window.location.href = 'auth.html';
  }
};
