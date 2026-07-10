const SUPPORTED_LANGS = ["nl", "en", "ro", "sv", "no"];

const I18n = {
  lang: null,
  dict: {},

  async load(lang) {
    this.lang = SUPPORTED_LANGS.includes(lang) ? lang : "en";
    const res = await fetch(`/assets/i18n/${this.lang}.json`);
    this.dict = await res.json();
    document.documentElement.lang = this.lang;
  },

  t(key, vars) {
    let val = this.dict[key];
    if (val === undefined) return key;
    if (vars) {
      Object.entries(vars).forEach(([k, v]) => {
        val = val.replace(`{${k}}`, v);
      });
    }
    return val;
  },

  deptLabel(name) {
    return (this.dict.departments && this.dict.departments[name]) || name;
  },

  applyToDom(root) {
    root = root || document;
    root.querySelectorAll("[data-i18n]").forEach((el) => {
      el.textContent = this.t(el.getAttribute("data-i18n"));
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      el.setAttribute("placeholder", this.t(el.getAttribute("data-i18n-placeholder")));
    });
  },
};
