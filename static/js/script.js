/* ============================================================
   FinSight – script.js
   Premium UI Interactions & Animations
   Author : FinSight Dev Team
   ============================================================ */

'use strict';

// ══════════════════════════════════════════════════════════════
//  1. CUSTOM CURSOR & MOUSE TRAIL
// ══════════════════════════════════════════════════════════════
(function initCursor() {
  const cursor = document.getElementById('cursor');
  const ring   = document.getElementById('cursor-ring');
  if (!cursor || !ring) return;

  let mouseX = 0, mouseY = 0;
  let ringX  = 0, ringY  = 0;

  const TRAIL_COUNT = 8;
  const trails = [];

  // Create trail dots
  for (let i = 0; i < TRAIL_COUNT; i++) {
    const dot = document.createElement('div');
    dot.className = 'trail-dot';
    dot.style.opacity  = ((TRAIL_COUNT - i) / TRAIL_COUNT * 0.5).toString();
    dot.style.width    = `${6 - i * 0.4}px`;
    dot.style.height   = `${6 - i * 0.4}px`;
    document.body.appendChild(dot);
    trails.push({ el: dot, x: 0, y: 0 });
  }

  document.addEventListener('mousemove', e => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    cursor.style.left = mouseX + 'px';
    cursor.style.top  = mouseY + 'px';
  });

  // Smooth ring + trail
  function animate() {
    ringX += (mouseX - ringX) * 0.12;
    ringY += (mouseY - ringY) * 0.12;
    ring.style.left = ringX + 'px';
    ring.style.top  = ringY + 'px';

    // Cascade trail
    let prevX = mouseX, prevY = mouseY;
    trails.forEach(t => {
      t.x += (prevX - t.x) * 0.25;
      t.y += (prevY - t.y) * 0.25;
      t.el.style.left = t.x + 'px';
      t.el.style.top  = t.y + 'px';
      prevX = t.x;
      prevY = t.y;
    });

    requestAnimationFrame(animate);
  }
  animate();

  // Hover enlarge
  document.querySelectorAll('a, button, input, label, .stat-card').forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.width  = '20px';
      cursor.style.height = '20px';
      cursor.style.background = 'var(--accent)';
      ring.style.width  = '60px';
      ring.style.height = '60px';
      ring.style.borderColor = 'rgba(0,212,170,0.5)';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.width  = '12px';
      cursor.style.height = '12px';
      cursor.style.background = 'var(--primary)';
      ring.style.width  = '40px';
      ring.style.height = '40px';
      ring.style.borderColor = 'rgba(108,99,255,0.6)';
    });
  });
})();


// ══════════════════════════════════════════════════════════════
//  2. PARTICLE BACKGROUND (Canvas)
// ══════════════════════════════════════════════════════════════
(function initParticles() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W = canvas.width  = window.innerWidth;
  let H = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });

  const PARTICLE_COUNT = 60;
  const particles = [];

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x  = Math.random() * W;
      this.y  = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.4;
      this.vy = (Math.random() - 0.5) * 0.4;
      this.r  = Math.random() * 1.5 + 0.5;
      this.alpha = Math.random() * 0.5 + 0.1;
      this.color = Math.random() > 0.5
        ? `rgba(108,99,255,${this.alpha})`
        : `rgba(0,212,170,${this.alpha})`;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > W) this.vx *= -1;
      if (this.y < 0 || this.y > H) this.vy *= -1;
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = this.color;
      ctx.fill();
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(new Particle());
  }

  // Connect nearby particles
  function connectParticles() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          const alpha = (1 - dist / 120) * 0.08;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(108,99,255,${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => { p.update(); p.draw(); });
    connectParticles();
    requestAnimationFrame(loop);
  }
  loop();
})();


// ══════════════════════════════════════════════════════════════
//  3. PASSWORD TOGGLE (Show / Hide)
// ══════════════════════════════════════════════════════════════
function initPasswordToggle(inputId, toggleId) {
  const input  = document.getElementById(inputId);
  const toggle = document.getElementById(toggleId);
  if (!input || !toggle) return;

  toggle.addEventListener('click', () => {
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    toggle.innerHTML = isHidden
      ? '<i class="bi bi-eye-slash-fill"></i>'
      : '<i class="bi bi-eye-fill"></i>';
    toggle.title = isHidden ? 'Hide password' : 'Show password';
  });
}

initPasswordToggle('password',         'toggle-password');
initPasswordToggle('confirm_password', 'toggle-confirm');


// ══════════════════════════════════════════════════════════════
//  4. PASSWORD STRENGTH METER
// ══════════════════════════════════════════════════════════════
(function initStrengthMeter() {
  const input = document.getElementById('password');
  if (!input) return;

  const bars  = document.querySelectorAll('.strength-bar');
  const label = document.getElementById('strength-label');
  const rules = {
    minLen:   { el: document.getElementById('rule-len'),     regex: /^.{8,}$/ },
    upper:    { el: document.getElementById('rule-upper'),   regex: /[A-Z]/ },
    lower:    { el: document.getElementById('rule-lower'),   regex: /[a-z]/ },
    number:   { el: document.getElementById('rule-number'),  regex: /[0-9]/ },
    special:  { el: document.getElementById('rule-special'), regex: /[!@#$%^&*(),.?":{}|<>_\-\[\]\/\\]/ },
  };

  const levels = [
    { name: 'Very Weak', cls: 'active-weak',   count: 1, color: '#ff4d6d' },
    { name: 'Weak',      cls: 'active-weak',   count: 1, color: '#ff4d6d' },
    { name: 'Fair',      cls: 'active-fair',   count: 2, color: '#ffc107' },
    { name: 'Good',      cls: 'active-good',   count: 3, color: '#17c3b2' },
    { name: 'Strong',    cls: 'active-strong', count: 4, color: '#00d4aa' },
    { name: 'Very Strong',cls:'active-strong', count: 4, color: '#00d4aa' },
  ];

  input.addEventListener('input', () => {
    const val = input.value;
    let score = 0;

    Object.values(rules).forEach(r => {
      const met = r.regex.test(val);
      if (met) score++;
      if (r.el) {
        r.el.classList.toggle('met', met);
        const icon = r.el.querySelector('i');
        if (icon) {
          icon.className = met ? 'bi bi-check-circle-fill' : 'bi bi-circle';
        }
      }
    });

    // Extra point for length ≥ 12
    if (val.length >= 12) score = Math.min(score + 1, 5);

    const level = levels[Math.min(score, levels.length - 1)];
    const activeBars = level.count;

    bars.forEach((b, i) => {
      b.className = 'strength-bar';
      if (i < activeBars) b.classList.add(level.cls);
    });

    if (label) {
      label.textContent = val.length ? `Strength: ${level.name}` : '';
      label.style.color = level.color;
    }
  });
})();


// ══════════════════════════════════════════════════════════════
//  5. LIVE EMAIL VALIDATION
// ══════════════════════════════════════════════════════════════
(function initEmailValidation() {
  const emailInput = document.getElementById('email');
  const emailMsg   = document.getElementById('email-validation-msg');
  if (!emailInput) return;

  const emailRegex = /^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$/;

  emailInput.addEventListener('input', () => {
    const val = emailInput.value.trim();
    if (!val) {
      emailInput.classList.remove('is-valid', 'is-invalid');
      if (emailMsg) emailMsg.textContent = '';
      return;
    }
    const valid = emailRegex.test(val);
    emailInput.classList.toggle('is-valid',   valid);
    emailInput.classList.toggle('is-invalid', !valid);
    if (emailMsg) {
      emailMsg.textContent = valid
        ? '✓ Valid email address'
        : '✗ Please enter a valid email';
      emailMsg.className = `validation-msg ${valid ? 'valid' : 'invalid'}`;
    }
  });
})();


// ══════════════════════════════════════════════════════════════
//  6. PASSWORD MATCH VALIDATION
// ══════════════════════════════════════════════════════════════
(function initPasswordMatch() {
  const pw1 = document.getElementById('password');
  const pw2 = document.getElementById('confirm_password');
  const msg = document.getElementById('confirm-validation-msg');
  if (!pw1 || !pw2) return;

  function check() {
    const v1 = pw1.value;
    const v2 = pw2.value;
    if (!v2) {
      pw2.classList.remove('is-valid', 'is-invalid');
      if (msg) msg.textContent = '';
      return;
    }
    const match = v1 === v2;
    pw2.classList.toggle('is-valid',   match);
    pw2.classList.toggle('is-invalid', !match);
    if (msg) {
      msg.textContent = match ? '✓ Passwords match' : '✗ Passwords do not match';
      msg.className = `validation-msg ${match ? 'valid' : 'invalid'}`;
    }
  }

  pw1.addEventListener('input', check);
  pw2.addEventListener('input', check);
})();


// ══════════════════════════════════════════════════════════════
//  7. FORM SUBMIT LOADING ANIMATION
// ══════════════════════════════════════════════════════════════
(function initFormLoading() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
      const btn = this.querySelector('.btn-primary-custom');
      if (!btn) return;

      // Basic HTML5 check first
      if (!this.checkValidity()) return;

      btn.disabled = true;
      const originalHTML = btn.innerHTML;
      btn.innerHTML = '<span class="btn-spinner"></span>Processing…';

      // Safety: re-enable after 8s in case something breaks
      setTimeout(() => {
        btn.disabled  = false;
        btn.innerHTML = originalHTML;
      }, 8000);
    });
  });
})();


// ══════════════════════════════════════════════════════════════
//  8. BUTTON RIPPLE EFFECT
// ══════════════════════════════════════════════════════════════
document.querySelectorAll('.btn-primary-custom').forEach(btn => {
  btn.addEventListener('click', function(e) {
    const rect   = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className  = 'btn-ripple';
    ripple.style.left = (e.clientX - rect.left) + 'px';
    ripple.style.top  = (e.clientY - rect.top)  + 'px';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
});


// ══════════════════════════════════════════════════════════════
//  9. ALERT AUTO-DISMISS
// ══════════════════════════════════════════════════════════════
document.querySelectorAll('.alert-custom').forEach(alert => {
  const closeBtn = alert.querySelector('.alert-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      alert.style.opacity  = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 300);
    });
  }
  // Auto-dismiss after 6 seconds
  setTimeout(() => {
    if (alert.parentNode) {
      alert.style.transition = 'opacity 0.4s, transform 0.4s';
      alert.style.opacity    = '0';
      alert.style.transform  = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 400);
    }
  }, 6000);
});


// ══════════════════════════════════════════════════════════════
//  10. SUCCESS POPUP (Registration)
// ══════════════════════════════════════════════════════════════
(function initSuccessPopup() {
  const overlay  = document.getElementById('success-popup');
  if (!overlay) return;

  overlay.classList.add('active');

  let sec = 3;
  const countdownEl = document.getElementById('popup-countdown');

  const interval = setInterval(() => {
    sec--;
    if (countdownEl) countdownEl.textContent = `Redirecting to login in ${sec}s…`;
    if (sec <= 0) {
      clearInterval(interval);
      window.location.href = overlay.dataset.redirect || '/login';
    }
  }, 1000);

  // Allow manual close
  const closeBtn = document.getElementById('popup-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      clearInterval(interval);
      overlay.classList.remove('active');
    });
  }
})();


// ══════════════════════════════════════════════════════════════
//  11. PAGE TRANSITION
// ══════════════════════════════════════════════════════════════
(function initPageTransitions() {
  const overlay = document.getElementById('page-transition');
  if (!overlay) return;

  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:')) return;

    link.addEventListener('click', function(e) {
      e.preventDefault();
      const dest = this.href;
      overlay.classList.add('active');
      setTimeout(() => { window.location.href = dest; }, 380);
    });
  });
})();


// ══════════════════════════════════════════════════════════════
//  12. TYPING EFFECT (Dashboard greeting)
// ══════════════════════════════════════════════════════════════
(function initTypingEffect() {
  const el = document.getElementById('typing-text');
  if (!el) return;

  const phrases = [
    'Track your expenses 💰',
    'Monitor investments 📈',
    'Achieve financial goals 🎯',
    'Build your wealth 🚀',
  ];
  let pi = 0, ci = 0;
  let typing = true;

  function type() {
    const phrase = phrases[pi];
    if (typing) {
      el.textContent = phrase.substring(0, ci + 1);
      ci++;
      if (ci === phrase.length) { typing = false; setTimeout(type, 1800); return; }
    } else {
      el.textContent = phrase.substring(0, ci - 1);
      ci--;
      if (ci === 0) {
        typing = true;
        pi = (pi + 1) % phrases.length;
        setTimeout(type, 400);
        return;
      }
    }
    setTimeout(type, typing ? 60 : 35);
  }
  type();
})();


// ══════════════════════════════════════════════════════════════
//  13. STAT CARD COUNTER ANIMATION (Dashboard)
// ══════════════════════════════════════════════════════════════
(function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  counters.forEach(el => {
    const target   = parseFloat(el.dataset.count);
    const prefix   = el.dataset.prefix || '';
    const suffix   = el.dataset.suffix || '';
    const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;
    let current    = 0;
    const step     = target / 60;

    function update() {
      current = Math.min(current + step, target);
      el.textContent = prefix + current.toFixed(decimals) + suffix;
      if (current < target) requestAnimationFrame(update);
    }
    // Trigger when visible
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) { update(); observer.disconnect(); }
    });
    observer.observe(el);
  });
})();


// ══════════════════════════════════════════════════════════════
//  14. FLOATING ICONS GENERATOR
// ══════════════════════════════════════════════════════════════
(function initFloatingIcons() {
  const container = document.getElementById('floating-icons');
  if (!container) return;

  const icons = ['💰','📈','💳','💵','🪙','📊','💹','🏦','💎','📉','🎯','💡'];
  icons.forEach((icon, i) => {
    const el = document.createElement('div');
    el.className = 'float-icon';
    el.textContent = icon;
    el.style.cssText = `
      left:  ${Math.random() * 90 + 5}%;
      top:   ${Math.random() * 90 + 5}%;
      --dur:  ${10 + Math.random() * 10}s;
      --delay:${(i * 1.5)}s;
      font-size: ${1.5 + Math.random()}rem;
    `;
    container.appendChild(el);
  });
})();


// ══════════════════════════════════════════════════════════════
//  15. CURSOR GLOW ON CARDS
// ══════════════════════════════════════════════════════════════
document.querySelectorAll('.glass-card, .stat-card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x    = ((e.clientX - rect.left) / rect.width)  * 100;
    const y    = ((e.clientY - rect.top)  / rect.height) * 100;
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
  });
});


// ══════════════════════════════════════════════════════════════
//  16. FORM NAME VALIDATION (Register)
// ══════════════════════════════════════════════════════════════
(function initNameValidation() {
  const nameInput = document.getElementById('name');
  const nameMsg   = document.getElementById('name-validation-msg');
  if (!nameInput) return;

  nameInput.addEventListener('input', () => {
    const val = nameInput.value.trim();
    const valid = val.length >= 2 && /^[a-zA-Z\s'.-]+$/.test(val);
    nameInput.classList.toggle('is-valid',   valid && val.length > 0);
    nameInput.classList.toggle('is-invalid', !valid && val.length > 0);
    if (nameMsg) {
      nameMsg.textContent = val.length === 0 ? ''
        : valid ? '✓ Valid name' : '✗ Please enter your full name';
      nameMsg.className = `validation-msg ${valid ? 'valid' : 'invalid'}`;
    }
  });
})();


// ══════════════════════════════════════════════════════════════
//  17. DARK / LIGHT THEME TOGGLE
//  Persists across all pages using localStorage
// ══════════════════════════════════════════════════════════════
(function initThemeToggle() {
  const pill  = document.getElementById('theme-pill');
  const thumb = document.getElementById('theme-pill-thumb');
  const label = document.getElementById('theme-pill-label');
  if (!pill) return;

  const STORAGE_KEY = 'finsight_theme';
  let isLight = localStorage.getItem(STORAGE_KEY) === 'light';

  /* Apply theme without animation first (on load) */
  if (isLight) applyTheme(true, false);

  pill.addEventListener('click', () => {
    isLight = !isLight;
    localStorage.setItem(STORAGE_KEY, isLight ? 'light' : 'dark');
    applyTheme(isLight, true);
  });

  function applyTheme(light, animate) {
    if (!animate) {
      document.body.style.transition = 'none';
    }

    document.body.classList.toggle('light-mode', light);
    pill.classList.toggle('light-active', light);

    if (light) {
      if (thumb) thumb.textContent = '☀️';
      if (label) label.textContent = 'Light';
    } else {
      if (thumb) thumb.textContent = '🌙';
      if (label) label.textContent = 'Dark';
    }

    /* Subtle scale animation on pill */
    if (animate) {
      pill.style.transform = 'translateY(-1px) scale(0.95)';
      setTimeout(() => { pill.style.transform = ''; }, 200);
    }

    if (!animate) {
      /* Re-enable transitions after first paint */
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          document.body.style.transition = '';
        });
      });
    }
  }
})();

