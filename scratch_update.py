import re

with open('d:/Desktop/projects/MindHaven/frontend/breathe.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 2. Add theme-color
text = text.replace('<head>', '<head>\n  <meta name="theme-color" content="#120F17">')

# 3. Add ScrollTrigger CDN
text = text.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>', 
                    '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>\n  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>')

# 4. Update Google Fonts link
text = text.replace('<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet"/>',
                    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet"/>')

# Also add theme.js script in head
text = text.replace('</head>', '  <script src="js/theme.js"></script>\n</head>')

# 5. Body
text = re.sub(r'<body style="background:#fcf9f8; min-height:100vh; overflow-x:hidden; color:#1c1b1b;">', '<body>', text)

# 6. Replace in <style>
style_block_match = re.search(r'<style>(.*?)</style>', text, re.DOTALL)
if style_block_match:
    style = style_block_match.group(1)
    # manual replacements inside style
    style = style.replace('color: #6b38d4;', 'color: var(--col-primary);')
    style = style.replace('color: #6f46b9;', 'color: var(--col-secondary);')
    style = style.replace('color: #1c1b1b;', 'color: var(--col-text-primary);')
    style = style.replace('color: #5d5a69;', 'color: var(--col-text-tertiary);')
    
    style = style.replace('background: rgba(107,56,212,0.12);', 'background: rgba(124,58,237,0.1);')
    style = style.replace('background: rgba(111,70,185,0.12);', 'background: rgba(168,85,247,0.1);')
    style = style.replace('background: rgba(93,90,105,0.1);', 'background: rgba(107,100,132,0.1);')
    style = style.replace('background: rgba(107,56,212,0.18);', 'background: rgba(124,58,237,0.18);')
    style = style.replace('background: #6b38d4;', 'background: var(--col-primary);')
    style = style.replace('background: rgba(107,56,212,0.1);', 'background: rgba(124,58,237,0.1);')
    
    style = style.replace('background: rgba(255,255,255,0.35);', 'background: var(--col-glass-bg);')
    style = style.replace('border: 1.5px solid rgba(255,255,255,0.45);', 'border: 1.5px solid var(--col-glass-border);')
    style = style.replace('border-color: rgba(107,56,212,0.5) !important;', 'border-color: var(--col-border-active) !important;')
    style = style.replace('background: rgba(107,56,212,0.07) !important;', 'background: var(--col-glass-bg) !important;')
    
    style = style.replace('background: linear-gradient(135deg, #8455ef, #6b38d4);', 'background: linear-gradient(135deg, var(--col-primary-glow), var(--col-primary));')
    
    style = style.replace('background: rgba(255,255,255,0.35);\n      color: #1c1b1b; font-weight: 800; font-size: 0.85rem;\n      border-radius: 16px; border: 1.5px solid rgba(255,255,255,0.6);',
                          'background: var(--col-glass-bg);\n      color: var(--col-text-primary); font-weight: 800; font-size: 0.85rem;\n      border-radius: 16px; border: 1.5px solid var(--col-glass-border);')
                          
    style = style.replace('background: rgba(255,255,255,0.6);', 'background: var(--col-glass-border);')
    
    style = style.replace("font-family: 'Plus Jakarta Sans', sans-serif;", 'font-family: var(--font-body);')
    
    text = text[:style_block_match.start(1)] + style + text[style_block_match.end(1):]


# 7. Header
header_old = 'background:rgba(252,249,248,0.35);border-bottom:1px solid rgba(255,255,255,0.22);'
header_new = 'background:var(--col-nav-bg);border-bottom:1px solid var(--col-border);'
text = text.replace(header_old, header_new)

# Theme toggle button
toggle_html = """
      <button onclick="toggleTheme()" class="theme-toggle" aria-label="Toggle theme">
        <span class="material-symbols-outlined theme-icon-light">light_mode</span>
        <span class="material-symbols-outlined theme-icon-dark">dark_mode</span>
      </button>
"""
text = re.sub(r'(<a href="insights\.html" style="display:flex;align-items:center;gap:6px;)', toggle_html + r'      \1', text)


# 8. Inline hardcoded colors replace in body
text = re.sub(r'color:\s*#1c1b1b', 'color:var(--col-text-primary)', text)
text = re.sub(r'color:\s*#494454', 'color:var(--col-text-secondary)', text)
text = re.sub(r'color:\s*#6b38d4', 'color:var(--col-primary)', text)
text = re.sub(r'background:\s*#8455ef', 'background:var(--col-primary-glow)', text)

# tgrid, studio-grid, overview-grid etc -> add scroll-section
text = text.replace('id="tgrid" style=', 'id="tgrid" class="scroll-section" style=')
text = text.replace('id="studio-grid"', 'id="studio-grid" class="scroll-section"')
text = text.replace('<section style="margin-top:56px;">', '<section class="scroll-section" style="margin-top:56px;">')
text = text.replace('<div style="text-align:center;margin-bottom:36px;">', '<div class="scroll-section" style="text-align:center;margin-bottom:36px;">')

text = text.replace('border:1.5px solid rgba(255,255,255,0.5)', 'border:1.5px solid var(--col-glass-border)')
text = text.replace('background:rgba(255,255,255,0.35)', 'background:var(--col-glass-bg)')
text = text.replace('background:rgba(255,255,255,0.38)', 'background:var(--col-glass-bg)')
text = text.replace('background:rgba(107,56,212,0.06)', 'background:var(--col-glass-bg)')
text = text.replace('border:1.5px solid rgba(107,56,212,0.16)', 'border:1.5px solid var(--col-glass-border)')

# 9. Add gradual-blur.js
text = text.replace('</body>', '  <script src="js/gradual-blur.js"></script>\n</body>')

# Add GSAP setup
gsap_code = """
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
          gsap.registerPlugin(ScrollTrigger);
          gsap.utils.toArray('.scroll-section').forEach(sec => {
            gsap.from(sec, {
              scrollTrigger: {
                trigger: sec,
                start: 'top 85%',
              },
              y: 40,
              opacity: 0,
              duration: 0.8,
              ease: 'power3.out'
            });
          });
      }
      if (typeof createGradualBlur !== "undefined") {
        createGradualBlur(document.querySelector('.fixed.inset-0'), { position: 'bottom', strength: 2, height: '6rem', divCount: 5, curve: 'bezier' });
      }
    });
  </script>
</body>
"""
text = text.replace('</body>', gsap_code)

# 11. Mobile nav colors
text = text.replace('text-on-surface-variant/80', 'text-[var(--col-text-secondary)]')
text = text.replace('hover:text-primary', 'hover:text-[var(--col-primary)]')
text = text.replace('text-primary', 'text-[var(--col-primary)]')
text = text.replace('bg-white/60', 'bg-[var(--col-nav-bg)]')
text = text.replace('border-white/20', 'border-[var(--col-glass-border)]')


with open('d:/Desktop/projects/MindHaven/frontend/breathe_new.html', 'w', encoding='utf-8') as f:
    f.write(text)
