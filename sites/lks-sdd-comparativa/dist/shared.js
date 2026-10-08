'use strict';
(() => {
  const button = document.getElementById('theme');
  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    button?.setAttribute('aria-label', theme === 'dark' ? 'Activar tema claro' : 'Activar tema oscuro');
    try { localStorage.setItem('lks-comparison-theme', theme); } catch {}
  }
  try { if (localStorage.getItem('lks-comparison-theme') === 'dark') setTheme('dark'); } catch {}
  button?.addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
  const selector = document.querySelector('.comparison-switcher');
  if (selector) {
    const resize = () => document.documentElement.style.setProperty('--selector-height', `${Math.ceil(selector.getBoundingClientRect().height)}px`);
    resize();
    new ResizeObserver(resize).observe(selector);
  }
  // Keep links from the original one-page comparison usable.
  if (document.body.classList.contains('home-page') && ['#ejecucion','#definicion','#gobierno','#calidad','#evolucion','#comparativa'].includes(location.hash)) {
    location.replace('kiro-spec.html' + location.hash);
  }
})();
