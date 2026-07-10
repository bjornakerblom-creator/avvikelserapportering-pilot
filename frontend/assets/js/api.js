const API_BASE = "/api";

async function _readError(res) {
  let detail = `HTTP ${res.status}`;
  try {
    const j = await res.json();
    if (j && j.detail) detail = j.detail;
  } catch (e) {
    /* ignore */
  }
  return new Error(detail);
}

const Api = {
  async get(path, params) {
    const url = new URL(API_BASE + path, window.location.origin);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
      });
    }
    const res = await fetch(url);
    if (!res.ok) throw await _readError(res);
    return res.json();
  },

  async postForm(path, formData) {
    const res = await fetch(API_BASE + path, { method: "POST", body: formData });
    if (!res.ok) throw await _readError(res);
    return res.json();
  },

  attachmentUrl(ticketId, attachmentId) {
    return `${API_BASE}/tickets/${ticketId}/attachments/${attachmentId}`;
  },

  exportCsvUrl(params) {
    const url = new URL(API_BASE + "/stats/export.csv", window.location.origin);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
      });
    }
    return url.toString();
  },
};
