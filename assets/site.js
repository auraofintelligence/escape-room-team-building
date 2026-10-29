const menuButton = document.querySelector('[data-menu]');
const allNav = document.getElementById('all-nav');
if (menuButton && allNav) {
  menuButton.addEventListener('click', () => {
    allNav.hidden = !allNav.hidden;
    menuButton.setAttribute('aria-expanded', String(!allNav.hidden));
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !allNav.hidden) {
      allNav.hidden = true;
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.focus();
    }
  });
}
document.querySelector('[data-top]')?.addEventListener('click', () => window.scrollTo({top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'}));
document.querySelectorAll('[data-filter]').forEach(input => {
  input.addEventListener('input', () => {
    let count = 0;
    document.querySelectorAll('[data-search]').forEach(item => {
      item.hidden = !item.dataset.search.toLowerCase().includes(input.value.toLowerCase().trim());
      if (!item.hidden) count++;
    });
    const status = document.querySelector('[data-count]');
    if (status) status.textContent = count + ' matching entries';
    const empty = document.querySelector('[data-empty]');
    if (empty) empty.hidden = count > 0;
  });
});
const slides = [...document.querySelectorAll('.presentation-card')];
if (slides.length) {
  let current = 0;
  const toggle = document.querySelector('[data-present]');
  const show = target => {
    current = Math.max(0, Math.min(slides.length - 1, target));
    slides.forEach((slide, index) => slide.classList.toggle('active', index === current));
    document.querySelector('[data-slide-count]').textContent = (current + 1) + ' / ' + slides.length;
    document.querySelector('[data-prev]').disabled = current === 0;
    document.querySelector('[data-next]').disabled = current === slides.length - 1;
  };
  toggle.addEventListener('click', () => {
    const active = document.body.classList.toggle('presentation-mode');
    toggle.textContent = active ? 'Return to outline' : 'Start presentation';
    show(current);
    if (active) window.scrollTo({top: 0, behavior: 'instant'});
  });
  document.querySelector('[data-prev]').addEventListener('click', () => show(current - 1));
  document.querySelector('[data-next]').addEventListener('click', () => show(current + 1));
  document.addEventListener('keydown', event => {
    if (!document.body.classList.contains('presentation-mode') || event.target.matches('input, textarea')) return;
    if (event.key === 'ArrowRight') show(current + 1);
    if (event.key === 'ArrowLeft') show(current - 1);
    if (event.key === 'Escape') {
      document.body.classList.remove('presentation-mode');
      toggle.textContent = 'Start presentation';
    }
  });
  show(0);
}
