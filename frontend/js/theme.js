/* ═══════════════════════════════════════════════════════════════
   js/theme.js  —  Shared Tailwind config + CSS vars
   Include this BEFORE tailwind.config assignment on every page.
═══════════════════════════════════════════════════════════════ */

/* Called inline as: <script>applyTailwindTheme()</script>
   after the tailwind CDN script tag.                          */

(function () {
  if (typeof tailwind === 'undefined') return;

  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          'primary':                  '#6b38d4',
          'secondary':                '#6f46b9',
          'tertiary':                 '#5d5a69',
          'background':               '#fcf9f8',
          'surface':                  '#fcf9f8',
          'surface-bright':           '#fcf9f8',
          'surface-dim':              '#dcd9d9',
          'surface-container':        '#f0eded',
          'surface-container-low':    '#f6f3f2',
          'surface-container-high':   '#eae7e7',
          'surface-container-highest':'#e5e2e1',
          'surface-container-lowest': '#ffffff',
          'on-surface':               '#1c1b1b',
          'on-surface-variant':       '#494454',
          'on-background':            '#1c1b1b',
          'on-primary':               '#ffffff',
          'on-secondary':             '#ffffff',
          'on-tertiary':              '#ffffff',
          'primary-container':        '#8455ef',
          'secondary-container':      '#b188ff',
          'primary-fixed':            '#e9ddff',
          'primary-fixed-dim':        '#d0bcff',
          'secondary-fixed':          '#ebdcff',
          'secondary-fixed-dim':      '#d3bbff',
          'inverse-primary':          '#d0bcff',
          'inverse-surface':          '#313030',
          'inverse-on-surface':       '#f3f0ef',
          'outline':                  '#7b7486',
          'outline-variant':          '#cbc3d7',
          'surface-tint':             '#6d3bd7',
          'error':                    '#ba1a1a',
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
          'body-md':  ['Plus Jakarta Sans', 'sans-serif'],
          'title-md': ['Plus Jakarta Sans', 'sans-serif'],
        },
      },
    },
  };
})();
