const Prefs = {
  KEY: "avvikelser_prefs",

  get() {
    try {
      return JSON.parse(localStorage.getItem(this.KEY)) || {};
    } catch (e) {
      return {};
    }
  },

  set(patch) {
    const cur = this.get();
    localStorage.setItem(this.KEY, JSON.stringify({ ...cur, ...patch }));
  },
};

function requireOnboarding() {
  const p = Prefs.get();
  if (!p.lang || !p.organizationId) {
    window.location.href = "/index.html";
    return true;
  }
  return false;
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const datePart = d.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit" });
  const timePart = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  return `${datePart} ${timePart}`;
}

function toast(msg) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove("show"), 3000);
}

function typeBadgeLabel(type, subtype) {
  if (type === "customer_complaint") return I18n.t("type_customer_complaint");
  if (subtype === "deviation") return I18n.t("subtype_deviation");
  if (subtype === "disruption") return I18n.t("subtype_disruption");
  return I18n.t("type_internal");
}
