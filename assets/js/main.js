/* =========================================================
   株式会社RISE 提案用デモサイト - main.js
   依存ライブラリなし / 軽量・モバイル配慮
   ========================================================= */
(() => {
  "use strict";

  const root = document.documentElement;
  const body = document.body;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- ページ表示・遷移演出 ---------- */
  const markLoaded = () => requestAnimationFrame(() => root.classList.add("is-loaded"));
  if (document.readyState === "complete") markLoaded();
  else window.addEventListener("load", markLoaded);
  // 画像読み込みが遅い場合でも 1.2 秒で幕を開ける
  setTimeout(markLoaded, 1200);

  // 戻る操作(bfcache)で幕が閉じたままにならないように
  window.addEventListener("pageshow", (e) => {
    if (e.persisted) root.classList.remove("is-leaving");
  });

  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a || reduceMotion) return;
    const href = a.getAttribute("href");
    if (
      e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0 ||
      a.target === "_blank" || a.hasAttribute("download") ||
      !href || href.startsWith("#") || /^(mailto|tel|https?):/.test(href)
    ) return;
    const url = new URL(a.href, location.href);
    // 同一ページ内アンカーは通常スクロール
    if (url.pathname === location.pathname && url.hash) return;
    e.preventDefault();
    root.classList.add("is-leaving");
    setTimeout(() => { location.href = a.href; }, 520);
  });

  /* ---------- ヘッダー ---------- */
  const header = document.querySelector("[data-header]");
  const pagetop = document.querySelector("[data-pagetop]");
  let lastY = window.scrollY;
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle("is-scrolled", y > 40);
    // 下スクロールで隠し、上スクロールで表示
    const menuOpen = header.classList.contains("is-open");
    header.classList.toggle("is-hidden", !menuOpen && y > 400 && y > lastY);
    pagetop && pagetop.classList.toggle("is-show", y > 600);
    lastY = y;
    ticking = false;
  };
  window.addEventListener("scroll", () => {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();

  /* ---------- モバイルメニュー ---------- */
  const toggle = document.querySelector("[data-menu-toggle]");
  const drawer = document.querySelector("[data-drawer]");
  const setMenu = (open) => {
    header.classList.toggle("is-open", open);
    body.classList.toggle("is-locked", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.querySelector(".visually-hidden").textContent = open ? "メニューを閉じる" : "メニューを開く";
    if (open) header.classList.remove("is-hidden");
  };
  toggle && toggle.addEventListener("click", () => setMenu(!header.classList.contains("is-open")));
  drawer && drawer.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && header.classList.contains("is-open")) { setMenu(false); toggle.focus(); }
  });
  window.matchMedia("(min-width: 1024px)").addEventListener("change", (m) => { if (m.matches) setMenu(false); });

  /* ---------- スクロール表示アニメーション ---------- */
  const revealEls = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-inview");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.12 });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("is-inview"));
  }

  /* ---------- パララックス（PCのみ・軽量） ---------- */
  const parallaxEls = document.querySelectorAll("[data-parallax]");
  if (parallaxEls.length && !reduceMotion && window.matchMedia("(min-width: 768px)").matches) {
    let pTicking = false;
    const update = () => {
      const vh = window.innerHeight;
      parallaxEls.forEach((el) => {
        const r = el.parentElement.getBoundingClientRect();
        if (r.bottom < 0 || r.top > vh) return;
        const progress = (r.top + r.height / 2 - vh / 2) / (vh + r.height);
        el.style.transform = `translate3d(0, ${progress * -120}px, 0)`;
      });
      pTicking = false;
    };
    window.addEventListener("scroll", () => {
      if (!pTicking) { requestAnimationFrame(update); pTicking = true; }
    }, { passive: true });
    update();
  }

  /* ---------- デモ用モーダル（送信・発信の無効化） ---------- */
  const modal = document.querySelector("[data-demo-modal]");
  let lastFocus = null;
  const openModal = (text) => {
    if (!modal) return;
    lastFocus = document.activeElement;
    modal.querySelector("[data-demo-text]").textContent = text;
    modal.hidden = false;
    body.classList.add("is-locked");
    modal.querySelector("button").focus();
  };
  const closeModal = () => {
    modal.hidden = true;
    body.classList.remove("is-locked");
    lastFocus && lastFocus.focus();
  };
  modal && modal.addEventListener("click", (e) => { if (e.target.closest("[data-demo-close]")) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && modal && !modal.hidden) closeModal(); });

  document.querySelectorAll('[data-demo-action="tel"]').forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      openModal("提案用デモのため、電話の発信は無効にしています。正式公開時はタップで発信できるようになります。");
    });
  });

  const form = document.querySelector("[data-demo-form]");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      // 入力チェックのみ実施（送信は一切行わない）
      let firstInvalid = null;
      form.querySelectorAll("[required]").forEach((field) => {
        const ok = field.type === "checkbox" ? field.checked : field.checkValidity() && field.value.trim() !== "";
        field.classList.toggle("is-invalid", !ok);
        field.setAttribute("aria-invalid", String(!ok));
        if (!ok && !firstInvalid) firstInvalid = field;
      });
      if (firstInvalid) {
        firstInvalid.focus();
        openModal("必須項目が未入力、または形式が正しくない項目があります。※デモのため、入力内容が送信されることはありません。");
        return;
      }
      openModal("入力チェックは完了しました。提案用デモのため、お問い合わせ内容は送信・保存されません。");
    });
    form.addEventListener("input", (e) => {
      if (e.target.classList.contains("is-invalid")) {
        e.target.classList.remove("is-invalid");
        e.target.removeAttribute("aria-invalid");
      }
    });
  }

  /* ---------- 施工実績の絞り込み ---------- */
  const filter = document.querySelector("[data-works-filter]");
  if (filter) {
    const cards = document.querySelectorAll("[data-works-grid] .work-card");
    const empty = document.querySelector("[data-works-empty]");
    filter.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-filter]");
      if (!btn) return;
      const key = btn.dataset.filter;
      filter.querySelectorAll("[data-filter]").forEach((b) => {
        const active = b === btn;
        b.classList.toggle("is-active", active);
        b.setAttribute("aria-pressed", String(active));
      });
      let visible = 0;
      cards.forEach((card) => {
        const show = key === "all" || card.dataset.category === key;
        card.classList.toggle("is-hidden", !show);
        card.classList.remove("is-filter-in");
        if (show) {
          visible++;
          card.classList.add("is-inview");
          void card.offsetWidth; // アニメーションを再生し直す
          card.classList.add("is-filter-in");
        }
      });
      if (empty) empty.hidden = visible > 0;
    });
  }
})();
