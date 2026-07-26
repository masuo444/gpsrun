/* ===== MANGA VIEWER =====
   ページ側で window.MANGA_CONFIG を定義してから読み込む。
   {lang, base, pages, w, h, i18n:{alt, prev, next, jump}} */
(function () {
  var C = window.MANGA_CONFIG;
  if (!C) return;

  var reader = document.getElementById('mvReader');
  var fill = document.getElementById('mvFill');
  var track = document.getElementById('mvTrack');
  var cur = document.getElementById('mvCur');
  var pager = document.getElementById('mvPager');
  var btnPrev = document.getElementById('mvPrev');
  var btnNext = document.getElementById('mvNext');
  var jump = document.getElementById('mvJump');
  var btnFs = document.getElementById('mvFs');
  if (!reader) return;

  var MODE_KEY = 'gpsrun-manga-mode';
  var total = C.pages;
  var index = 1;              // 1-origin の現在ページ
  var mode = 'scroll';
  var els = [];

  /* ---------- ページを組み立てる ---------- */
  for (var i = 1; i <= total; i++) {
    var nn = i < 10 ? '0' + i : '' + i;
    var fig = document.createElement('div');
    fig.className = 'mv-page';
    fig.id = 'p' + i;
    fig.style.aspectRatio = C.w + ' / ' + C.h;
    var img = document.createElement('img');
    img.src = C.base + nn + '.webp';
    img.width = C.w;
    img.height = C.h;
    img.alt = C.i18n.alt.replace('{n}', i);
    // 最初の2ページは即時、それ以降は遅延読み込み
    img.loading = i <= 2 ? 'eager' : 'lazy';
    img.decoding = 'async';
    if (i <= 2) img.setAttribute('fetchpriority', 'high');
    fig.appendChild(img);
    var no = document.createElement('span');
    no.className = 'mv-page-no';
    no.textContent = i + ' / ' + total;
    fig.appendChild(no);
    reader.appendChild(fig);
    els.push(fig);
  }

  /* ---------- 表示更新 ---------- */
  function paint() {
    cur.textContent = index;
    fill.style.width = (index / total * 100) + '%';
    track.setAttribute('aria-valuenow', index);
    if (jump && document.activeElement !== jump) jump.value = index;
    if (btnPrev) btnPrev.disabled = index <= 1;
    if (btnNext) btnNext.disabled = index >= total;
    // ヘッダーの言語切替に現在ページを引き継ぐ
    document.querySelectorAll('.lang-menu a[data-mangahref]').forEach(function (a) {
      a.href = a.getAttribute('data-mangahref') + '#p' + index;
    });
  }

  function barOffset() {
    var bar = document.querySelector('.mv-bar');
    var h = bar ? bar.offsetHeight : 0;
    var top = bar ? parseFloat(getComputedStyle(bar).top) || 0 : 0;
    return h + top + 8;
  }

  function scrollToY(y, smooth) {
    y = Math.max(0, y);
    // 遠くへ飛ぶときのスムーススクロールは待ち時間が長すぎるので瞬時に移動する
    var far = Math.abs(y - window.scrollY) > window.innerHeight * 3;
    window.scrollTo({ top: y, behavior: (smooth === false || far) ? 'auto' : 'smooth' });
  }

  function goto(n, smooth) {
    n = Math.min(total, Math.max(1, n));
    index = n;
    if (mode === 'page') {
      els.forEach(function (el, k) { el.classList.toggle('is-current', k === n - 1); });
      // 前後1ページを先読みしておく
      [n, n + 1].forEach(function (k) {
        var el = els[k]; if (el) el.querySelector('img').loading = 'eager';
      });
      // 表示ページの入れ替えで文書の高さが変わるため、レイアウト確定後に移動する
      requestAnimationFrame(function () {
        scrollToY(reader.offsetTop - barOffset(), false);
      });
    } else {
      scrollToY(els[n - 1].getBoundingClientRect().top + window.scrollY - barOffset(), smooth);
    }
    paint();
  }

  /* ---------- モード切替 ---------- */
  function setMode(m, keepPage) {
    mode = m;
    reader.setAttribute('data-mode', m);
    document.querySelectorAll('.mv-mode').forEach(function (b) {
      b.setAttribute('aria-pressed', b.dataset.mode === m ? 'true' : 'false');
    });
    try { localStorage.setItem(MODE_KEY, m); } catch (e) {}
    if (m === 'page') {
      els.forEach(function (el, k) { el.classList.toggle('is-current', k === index - 1); });
    } else {
      els.forEach(function (el) { el.classList.remove('is-current'); });
    }
    // モード切替は文書の高さが大きく変わるので、レイアウト確定を待ってから移動する
    if (keepPage !== false) requestAnimationFrame(function () { goto(index, false); });
    paint();
  }

  document.querySelectorAll('.mv-mode').forEach(function (b) {
    b.addEventListener('click', function () { setMode(b.dataset.mode); });
  });

  /* ---------- 縦スクロール時の現在ページ検出 ---------- */
  var io = new IntersectionObserver(function (entries) {
    if (mode !== 'scroll') return;
    var best = null;
    entries.forEach(function (en) {
      if (en.isIntersecting && (!best || en.intersectionRatio > best.intersectionRatio)) best = en;
    });
    if (!best) return;
    var n = els.indexOf(best.target) + 1;
    if (n && n !== index) { index = n; paint(); }
  }, { threshold: [0.1, 0.5, 0.9], rootMargin: '-25% 0px -45% 0px' });
  els.forEach(function (el) { io.observe(el); });

  /* ---------- 進捗バーをクリックでシーク ---------- */
  track.addEventListener('click', function (e) {
    var r = track.getBoundingClientRect();
    goto(Math.ceil((e.clientX - r.left) / r.width * total));
  });

  /* ---------- ページ送り ---------- */
  if (btnPrev) btnPrev.addEventListener('click', function () { goto(index - 1); });
  if (btnNext) btnNext.addEventListener('click', function () { goto(index + 1); });
  if (jump) {
    jump.max = total;
    jump.addEventListener('change', function () { goto(parseInt(jump.value, 10) || 1); });
  }

  document.addEventListener('keydown', function (e) {
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); goto(index + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); goto(index - 1); }
    else if (e.key === 'Escape' && document.fullscreenElement) document.exitFullscreen();
  });

  // ページモードのスワイプ／タップ
  var sx = 0, sy = 0, st = 0;
  reader.addEventListener('touchstart', function (e) {
    sx = e.changedTouches[0].clientX; sy = e.changedTouches[0].clientY; st = e.timeStamp;
  }, { passive: true });
  reader.addEventListener('touchend', function (e) {
    if (mode !== 'page') return;
    var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy;
    if (e.timeStamp - st < 600 && Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.6) {
      goto(dx < 0 ? index + 1 : index - 1);
    }
  }, { passive: true });
  reader.addEventListener('click', function (e) {
    if (mode !== 'page') return;
    var r = reader.getBoundingClientRect();
    goto((e.clientX - r.left) / r.width < 0.4 ? index - 1 : index + 1);
  });

  /* ---------- 没入（フルスクリーン）モード ---------- */
  if (btnFs) {
    btnFs.addEventListener('click', function () {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
      else document.body.classList.toggle('mv-immersive'); // 非対応環境のフォールバック
    });
  }
  document.addEventListener('fullscreenchange', function () {
    document.body.classList.toggle('mv-immersive', !!document.fullscreenElement);
    setTimeout(function () { goto(index, false); }, 60);
  });

  /* ---------- 起動 ---------- */
  var saved;
  try { saved = localStorage.getItem(MODE_KEY); } catch (e) {}
  var start = parseInt((location.hash.match(/^#p(\d+)$/) || [])[1], 10);
  if (start >= 1 && start <= total) index = start;
  setMode(saved === 'page' ? 'page' : 'scroll', false);
  paint();
  if (start) setTimeout(function () { goto(start, false); }, 120);

  // 他ページから #p12 形式のリンクで飛んできたとき（リロードなしのハッシュ変更）
  window.addEventListener('hashchange', function () {
    var n = parseInt((location.hash.match(/^#p(\d+)$/) || [])[1], 10);
    if (n >= 1 && n <= total) goto(n, false);
  });

  // ヒーローの「読む」ボタン
  document.querySelectorAll('[data-mv-start]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      goto(parseInt(a.getAttribute('data-mv-start'), 10) || 1);
    });
  });
})();
