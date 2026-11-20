// Mane: the booking form. It asks the server which times are free, shows only those, then saves the
// booking and opens WhatsApp with it filled in. system.js checks the fields; this sends them.
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const touch = matchMedia('(pointer: coarse)').matches;

/* ------------------------------------------------------------ sending
   The booking is saved first, then WhatsApp opens with it filled in. On a desktop a tab is opened inside the
   click (later it would be blocked as a popup) and sent to WhatsApp once the salon has the booking; on a phone
   the page itself goes to WhatsApp, which hands over to the app. */
function errorLine(el) {
  const id = (el.getAttribute('aria-describedby') || el.closest('fieldset')?.getAttribute('aria-describedby') || '')
    .split(/\s+/).find(x => document.getElementById(x)?.classList.contains('field__error'));
  return id && document.getElementById(id);
}

function showErrors(form, errors) {
  const bad = [];
  for (const [name, msg] of Object.entries(errors)) {
    const el = form.elements[name];
    const field = el instanceof RadioNodeList ? el[0] : el;
    const line = field ? errorLine(field) : document.getElementById(`b-${name}-err`);
    if (field && !(el instanceof RadioNodeList)) field.setAttribute('aria-invalid', 'true');
    if (line) { line.textContent = msg; line.hidden = false; }
    if (field) bad.push(field);
  }
  if (bad.length) bad[0].focus();
  return Object.keys(errors).length;
}

async function send(form, done) {
  const status = $('[data-form-status]', form);
  const button = $('[type="submit"]', form);
  const win = touch ? null : window.open('', '_blank');
  if (win) win.opener = null;
  const wait = setTimeout(() => { status.textContent = form.dataset.sending || '…'; }, 300);
  button.disabled = true; button.setAttribute('aria-busy', 'true');
  $$('.field__error', form).forEach(e => { if (!e.closest('.field')?.querySelector(':invalid')) e.hidden = true; });
  try {
    const res = await fetch(form.action, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    const data = await res.json().catch(() => ({}));
    clearTimeout(wait);
    if (!data.ok) {
      win?.close();
      const n = showErrors(form, data.errors || {});
      status.textContent = n ? (form.dataset.fix || '{n}').replace('{n}', n) : (form.dataset.failed || '');
      if (data.errors?.time) refresh();   // someone took the time: show what is still free
      return;
    }
    status.textContent = data.message + ' ';
    const a = document.createElement('a');
    a.href = data.url; a.rel = 'noopener'; a.target = '_blank'; a.textContent = 'WhatsApp';
    status.append(a);
    done?.();
    if (win) win.location.href = data.url; else location.href = data.url;
  } catch {
    clearTimeout(wait);
    win?.close();
    status.textContent = form.dataset.failed || '';
  } finally {
    button.disabled = false; button.removeAttribute('aria-busy');
  }
}

/* ------------------------------------------------------------ the booking form */
const form = $('#bookForm');
let refresh = () => {};
if (form) {
  const service = $('#b-service'), day = $('#b-day'), grid = $('#b-slot-grid'), none = $('#b-slot-none');
  const slotsBox = $('#b-slots'), sum = $('#b-sum');
  const chosen = () => service.selectedOptions[0];
  const master = () => form.elements.master.value;
  const masterName = () => {
    const r = $('input[name="master"]:checked', form);
    return r?.value === 'any' ? form.dataset.any : r?.dataset.name;
  };
  const fmtDay = iso => { const [y, m, d] = iso.split('-'); return `${d}.${m}`; };

  function summary() {
    const o = chosen(), time = $('input[name="time"]:checked', form)?.value;
    sum.textContent = o && time
      ? `${o.textContent.split(' · ')[0]} · ${masterName()} · ${fmtDay(day.value)} ${time} · ${o.dataset.price}` : '';
  }

  // only the masters who do this kind of service; a hidden choice falls back to "any"
  function masters() {
    const cat = chosen()?.dataset.cat;
    $$('#b-masters .choice[data-cat]').forEach(l => {
      const show = l.dataset.cat === cat;
      l.hidden = !show;
      if (!show && l.querySelector('input').checked) form.elements.master.value = 'any';
    });
  }

  let ask = 0;
  refresh = async function () {
    const keep = $('input[name="time"]:checked', form)?.value;
    const n = ++ask;
    slotsBox.setAttribute('aria-busy', 'true');
    const q = new URLSearchParams({ service: service.value, day: day.value });
    if (master() !== 'any') q.set('master', master());
    let data = { times: [] };
    try { data = await (await fetch(`${form.dataset.slots}?${q}`, { headers: { Accept: 'application/json' } })).json(); } catch {}
    if (n !== ask) return;   // a newer question was asked meanwhile
    slotsBox.setAttribute('aria-busy', 'false');
    grid.replaceChildren(...(data.times || []).map(t => {
      const l = document.createElement('label');
      l.className = 'choice choice--time';
      l.innerHTML = `<input type="radio" name="time" value="${t}" required>${t}`;
      if (t === keep) l.firstChild.checked = true;
      return l;
    }));
    none.hidden = !!data.times?.length;
    none.textContent = data.closed ? form.dataset.closed : form.dataset.none;
    summary();
  };

  service.addEventListener('change', () => { masters(); refresh(); });
  day.addEventListener('change', refresh);
  $('#b-masters').addEventListener('change', refresh);
  grid.addEventListener('change', () => { $('#b-time-err').hidden = true; summary(); });

  // a price row or a master on this page fills the form instead of reloading the page
  document.addEventListener('click', e => {
    const link = e.target.closest('[data-service], [data-master]');
    if (!link || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    e.preventDefault();
    if (link.dataset.service) {
      service.value = link.dataset.service;
      masters();
    } else {
      if (chosen()?.dataset.cat !== link.dataset.cat) {
        service.value = $(`option[data-cat="${link.dataset.cat}"]`, service).value;
        masters();
      }
      form.elements.master.value = link.dataset.master;
    }
    refresh();
    history.replaceState(null, '', '#book');
    $('#book').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
    service.focus({ preventScroll: true });
  });

  form.addEventListener('submit', e => {
    if (!$('input[name="time"]:checked', form)) {
      e.preventDefault();
      const err = $('#b-time-err');
      err.hidden = false;
      $('input[name="time"]', form)?.focus();
      return;
    }
    if (!form.checkValidity()) return;   // system.js shows the reasons under the fields
    e.preventDefault();
    send(form, () => { $('#b-note').value = ''; refresh(); });
  });

  masters();
  refresh();
}
