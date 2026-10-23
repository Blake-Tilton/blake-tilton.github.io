// Blake Tilton — portfolio
// Hash routes: #/<tab> or #/<tab>/<project>. One view and one project visible at a time.

(() => {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const narrow = matchMedia('(max-width: 860px)');

  // ---------- Routing ----------
  const views = $$('.view');
  const tabs = $$('.tab');
  const DEFAULT = 'home';

  function route() {
    const [tab = DEFAULT, project] = location.hash.replace(/^#\/?/, '').split('/');
    const view = views.find(v => v.dataset.view === tab) || views.find(v => v.dataset.view === DEFAULT);
    const name = view.dataset.view;

    views.forEach(v => v.classList.toggle('is-active', v === view));
    tabs.forEach(t => {
      if (t.dataset.tab === name) t.setAttribute('aria-current', 'page');
      else t.removeAttribute('aria-current');
    });

    const projects = $$('.project', view);
    if (projects.length) {
      const active = projects.find(p => p.dataset.project === project) || projects[0];
      projects.forEach(p => p.classList.toggle('is-active', p === active));
      $$('.card', view).forEach(c => {
        if (c.dataset.project === active.dataset.project) c.setAttribute('aria-current', 'true');
        else c.removeAttribute('aria-current');
      });
      // On phones the detail sits below the list; bring it up when a project is picked.
      if (project && narrow.matches) $('.detail', view).scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
    }

    pauseHiddenMedia();
    watchLoops();
    const title = name === DEFAULT ? '' : ` — ${tabs.find(t => t.dataset.tab === name)?.textContent}`;
    document.title = `Blake Tilton${title}`;
  }

  addEventListener('hashchange', route);

  // ---------- Video ----------
  // Title loops play only while on screen; reels never autoplay.
  const loopWatcher = 'IntersectionObserver' in window && new IntersectionObserver(entries => {
    entries.forEach(({ target, isIntersecting }) => {
      if (isIntersecting && !reduceMotion) target.play().catch(() => {});
      else target.pause();
    });
  }, { threshold: 0.25 });

  function watchLoops() {
    $$('video[data-loop]').forEach(v => {
      if (reduceMotion) { v.controls = true; return; }
      if (loopWatcher) { loopWatcher.unobserve(v); loopWatcher.observe(v); }
    });
  }

  function pauseHiddenMedia() {
    $$('video').forEach(v => {
      const project = v.closest('.project');
      const shown = v.closest('.view').classList.contains('is-active') && (!project || project.classList.contains('is-active'));
      if (!shown) v.pause();
    });
  }

  // ---------- Gallery filter ----------
  const chips = $$('.chip');
  chips.forEach(chip => chip.addEventListener('click', () => {
    const f = chip.dataset.filter;
    chips.forEach(c => c.setAttribute('aria-pressed', String(c === chip)));
    $$('.tile').forEach(t => { t.hidden = f !== 'all' && t.dataset.cat !== f; });
  }));

  // ---------- Lightbox ----------
  const lb = $('#lightbox');
  const lbImg = $('.lb-img', lb);
  const lbCap = $('.lb-cap', lb);
  const lbCount = $('.lb-count', lb);
  let items = [];
  let index = 0;

  function show(i) {
    index = (i + items.length) % items.length;
    const { href, caption } = items[index];
    lbImg.src = href;
    lbImg.alt = caption;
    lbCap.textContent = caption;
    lbCount.textContent = `${index + 1} / ${items.length}`;
    // warm the next one
    if (items.length > 1) new Image().src = items[(index + 1) % items.length].href;
  }

  $$('.tile a').forEach(a => a.addEventListener('click', e => {
    if (!lb.showModal) return; // no <dialog> support: follow the link to the image
    e.preventDefault();
    const set = a.dataset.set && $(`.set[data-set="${a.dataset.set}"]`);
    items = set
      ? $$('a', set).map(x => ({ href: x.getAttribute('href'), caption: x.dataset.caption }))
      : [{ href: a.getAttribute('href'), caption: a.dataset.caption }];
    lb.classList.toggle('has-set', items.length > 1);
    show(0);
    lb.showModal();
  }));

  lb.addEventListener('click', e => {
    const dir = e.target.closest('[data-lb]')?.dataset.lb;
    if (dir) show(index + (dir === 'next' ? 1 : -1));
    else if (e.target === lb || e.target.classList.contains('lb-frame')) lb.close();
  });
  lb.addEventListener('keydown', e => {
    if (items.length < 2) return;
    if (e.key === 'ArrowRight') show(index + 1);
    if (e.key === 'ArrowLeft') show(index - 1);
  });
  lb.addEventListener('close', () => { lbImg.removeAttribute('src'); });

  // ---------- Dialog close buttons ----------
  $$('dialog [data-close]').forEach(b => b.addEventListener('click', () => b.closest('dialog').close()));

  // ---------- Contact ----------
  const contact = $('#contact');
  const form = $('#contact-form');
  const status = $('.form-status', form);
  const send = $('button[type="submit"]', form);

  $$('[data-open-contact]').forEach(b => b.addEventListener('click', () => {
    status.textContent = '';
    contact.showModal();
    $('input[name="name"]', form).focus();
  }));
  contact.addEventListener('click', e => { if (e.target === contact) contact.close(); });

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const data = new FormData(form);
    data.append('page', location.href);
    status.textContent = 'Sending…';
    send.disabled = true;
    try {
      // URL-encoded body is a "simple" request: no CORS preflight, and Apps Script reads it as e.parameter.
      const res = await fetch(form.action, { method: 'POST', body: new URLSearchParams(data) });
      const json = await res.json();
      if (!json.ok) throw new Error(json.error || 'failed');
      form.reset();
      status.textContent = 'Got it. I’ll get back to you.';
    } catch {
      status.textContent = 'That didn’t go through. Try again in a minute.';
    } finally {
      send.disabled = false;
    }
  });

  route();
})();
