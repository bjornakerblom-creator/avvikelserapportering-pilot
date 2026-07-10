const NAV_ITEMS = [
  { key: "new-ticket", href: "/new-ticket.html", label: "nav_new", icon: "＋" },
  { key: "tickets", href: "/tickets.html", label: "nav_search", icon: "🔍" },
  { key: "stats", href: "/stats.html", label: "nav_stats", icon: "📊" },
];

function renderShell(active) {
  const header = document.createElement("header");
  header.className = "app-header";
  header.innerHTML = `
    <img src="/assets/img/logo-yellow.png" alt="Saferoad" class="app-logo" />
    <button class="icon-btn" id="settingsBtn" aria-label="Settings" title="Settings">⚙</button>
  `;
  document.body.insertBefore(header, document.body.firstChild);

  const nav = document.createElement("nav");
  nav.className = "bottom-nav";
  nav.innerHTML = NAV_ITEMS.map(
    (item) => `
    <a href="${item.href}" class="nav-item ${item.key === active ? "active" : ""}">
      <span class="nav-icon">${item.icon}</span>
      <span data-i18n="${item.label}"></span>
    </a>`
  ).join("");
  document.body.appendChild(nav);

  document.getElementById("settingsBtn").addEventListener("click", () => {
    window.location.href = "/index.html?edit=1";
  });
}
