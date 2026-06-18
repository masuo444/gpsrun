/* テーマ切替トグル（ダーク/ライト）＋ localStorage 記憶 */
(function () {
  var KEY = 'gpsrun-theme';
  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>';

  function current() { return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark'; }
  var btn;
  function render() { if (btn) btn.innerHTML = current() === 'light' ? MOON : SUN; }
  function set(t) {
    if (t === 'light') document.documentElement.setAttribute('data-theme', 'light');
    else document.documentElement.removeAttribute('data-theme');
    try { localStorage.setItem(KEY, t); } catch (e) {}
    render();
  }
  function init() {
    btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'ダーク/ライト切替');
    btn.addEventListener('click', function () { set(current() === 'light' ? 'dark' : 'light'); });
    document.body.appendChild(btn);
    render();
  }
  if (document.readyState !== 'loading') init();
  else document.addEventListener('DOMContentLoaded', init);
})();
