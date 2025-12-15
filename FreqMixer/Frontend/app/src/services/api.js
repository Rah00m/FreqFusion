// Use explicit backend base URL to avoid Vite dev-server 404s on /api/*
const API_BASE = (import.meta.env.VITE_API_BASE = "http://127.0.0.1:8000/api");

const handleResponse = async (res) => {
  if (!res.ok) {
    let message = "Request failed";
    try {
      const data = await res.json();
      message = data?.detail || data?.message || message;
    } catch (_) {}
    throw new Error(message);
  }
  return res.json();
};

const API = {
  uploadImage: async (imageId, file) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/upload/${imageId}`, {
      method: "POST",
      body: form,
    });
    return handleResponse(res);
  },

  convertToGrayscale: async (imageId) => {
    const res = await fetch(`${API_BASE}/images/${imageId}/grayscale`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  getImages: async () => {
    const res = await fetch(`${API_BASE}/images`);
    return handleResponse(res);
  },

  getImage: async (imageId) => {
    const res = await fetch(`${API_BASE}/images/${imageId}`);
    return handleResponse(res);
  },

  calculateFT: async (imageId) => {
    const res = await fetch(`${API_BASE}/ft/calculate/${imageId}`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  calculateAllFT: async () => {
    const res = await fetch(`${API_BASE}/ft/calculate-all`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  getComponent: async (imageId, component) => {
    const res = await fetch(`${API_BASE}/ft/component/${imageId}/${component}`);
    return handleResponse(res);
  },

  mixFT: async (payload) => {
    const res = await fetch(`${API_BASE}/ft/mix`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  getFTCache: async () => {
    const res = await fetch(`${API_BASE}/ft/cache`);
    return handleResponse(res);
  },

  deleteImage: async (imageId) => {
    const res = await fetch(`${API_BASE}/upload/${imageId}`, {
      method: "DELETE",
    });
    return handleResponse(res);
  },

  deleteAllImages: async () => {
    const res = await fetch(`${API_BASE}/upload/all`, {
      method: "DELETE",
    });
    return handleResponse(res);
  },

  resizeAll: async () => {
    const res = await fetch(`${API_BASE}/resize`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  getCommonSize: async () => {
    const res = await fetch(`${API_BASE}/common-size`);
    return handleResponse(res);
  },

  getStatus: async () => {
    const res = await fetch(`${API_BASE}/status`);
    return handleResponse(res);
  },
};

export default API;
