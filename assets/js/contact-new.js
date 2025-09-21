/* New, isolated integration for the Contact form on index.html
   - No dependency on previous form-handler.js
   - Works from both Flask (http://127.0.0.1:8000) and Live Server (5500/5501)
   - Robust validation + timeout + clear user feedback
*/
(function () {
  // Detect API base automatically; allow override via window.VIU_API_BASE
  function getApiBase() {
    if (window.VIU_API_BASE) return window.VIU_API_BASE.replace(/\/$/, '');
    // If served by Flask (same origin)
    if (location.port === '8000') return '/api';
    // Otherwise, assume local Flask dev server
    return 'http://127.0.0.1:8000/api';
  }

  const API_BASE = getApiBase();
  console.log('[contact-new] API_BASE =', API_BASE, '| page =', location.href);

  // Utility: show message in existing placeholders if present
  function showStatus(type, msg) {
    const loading = document.querySelector('#contactForm .loading');
    const err = document.querySelector('#contactForm .error-message');
    const ok = document.querySelector('#contactForm .sent-message');
    if (loading) loading.style.display = 'none';
    if (err) err.style.display = 'none';
    if (ok) ok.style.display = 'none';

    if (type === 'loading' && loading) {
      loading.textContent = msg || 'درخواست بھیجی جا رہی ہے...';
      loading.style.display = 'block';
    } else if (type === 'error' && err) {
      err.innerHTML = msg || 'نیٹ ورک میں خرابی، دوبارہ کوشش کریں';
      err.style.display = 'block';
    } else if (type === 'success' && ok) {
      ok.innerHTML = msg || 'آپ کا پیغام کامیابی سے بھیج دیا گیا';
      ok.style.display = 'block';
    } else {
      // Fallback alerts if placeholders missing
      if (type === 'error') alert(msg);
      if (type === 'success') alert(msg);
    }
  }

  // Basic validators
  function isEmail(v) {
    return /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(v || '');
  }

  function validatePayload(p) {
    const errs = [];
    if (!p.name || p.name.trim().length < 2) errs.push('براہ کرم درست نام درج کریں');
    if (!isEmail(p.email)) errs.push('براہ کرم درست ای میل درج کریں');
    if (!p.subject || p.subject.trim().length < 3) errs.push('براہ کرم موضوع درج کریں');
    if (!p.message || p.message.trim().length < 10) errs.push('براہ کرم کم از کم 10 حروف کا پیغام لکھیں');
    return errs;
  }

  async function submitContact(payload) {
    // Timeout with AbortController
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 15000); // 15s

    const res = await fetch(`${API_BASE}/submit-contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
    clearTimeout(t);
    return res;
  }

  function init() {
    const form = document.getElementById('contactForm');
    if (!form) {
      console.warn('[contact-new] contactForm not found');
      return;
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const data = new FormData(form);
      const payload = {
        name: (data.get('name') || '').toString().trim(),
        email: (data.get('email') || '').toString().trim(),
        subject: (data.get('subject') || '').toString().trim(),
        message: (data.get('message') || '').toString().trim(),
      };
      console.log('[contact-new] payload', payload);

      const errors = validatePayload(payload);
      if (errors.length) {
        showStatus('error', errors.join('<br>'));
        return;
      }

      showStatus('loading', 'بھیجا جا رہا ہے...');
      const submitBtn = form.querySelector('button[type="submit"]');
      const btnHtml = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'بھیجا جا رہا ہے...';
      }

      try {
        const res = await submitContact(payload);
        let json = null;
        try { json = await res.json(); } catch { json = null; }
        console.log('[contact-new] response', res.status, json);

        if (res.ok && json && json.success) {
          showStatus('success', json.message || 'آپ کا پیغام کامیابی سے بھیج دیا گیا');
          form.reset();
          const first = form.querySelector('input[name="name"]');
          if (first) first.focus();
        } else {
          const err = (json && (json.error || json.message)) || `سرور کی خرابی (status ${res.status})`;
          showStatus('error', err);
        }
      } catch (err) {
        console.error('[contact-new] network error', err);
        const msg = err && err.name === 'AbortError'
          ? 'نیٹ ورک سست ہے یا سرور جواب نہیں دے رہا۔ براہ کرم دوبارہ کوشش کریں۔'
          : 'نیٹ ورک کنکشن کی خرابی۔ یقینی بنائیں کہ سرور چل رہا ہے (http://127.0.0.1:8000)';
        showStatus('error', msg);
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = btnHtml || 'پیغام بھیجیں';
        }
      }
    });

    console.log('[contact-new] initialized');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

