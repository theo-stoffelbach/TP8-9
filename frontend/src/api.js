async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw Object.assign(new Error(body.detail || `HTTP ${res.status}`), { status: res.status, body });
  }
  return res.json();
}

export const api = {
  // Customers
  getCustomers: (email) =>
    request(`/api/customers/${email ? `?email=${encodeURIComponent(email)}` : ""}`),
  getCustomer: (id) => request(`/api/customers/${id}/`),
  getAddresses: (id) => request(`/api/customers/${id}/addresses/`),
  createCustomer: (data) =>
    request("/api/customers/", { method: "POST", body: JSON.stringify(data) }),
  updateCustomer: (id, data) =>
    request(`/api/customers/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  createAddress: (customerId, data) =>
    request(`/api/customers/${customerId}/addresses/`, { method: "POST", body: JSON.stringify(data) }),
  updateAddress: (customerId, addressId, data) =>
    request(`/api/customers/${customerId}/addresses/${addressId}/`, { method: "PATCH", body: JSON.stringify(data) }),

  // Catalog
  getCategories: () => request("/api/categories/"),
  getProducts: ({ search = "", categoryId = "", activeOnly = true } = {}) => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (categoryId) params.set("category", categoryId);
    if (activeOnly) params.set("is_active", "true");
    const qs = params.toString();
    return request(`/api/products/${qs ? `?${qs}` : ""}`);
  },

  // Orders
  getOrders: () => request("/api/orders/"),
  createOrder: (data) =>
    request("/api/orders/", { method: "POST", body: JSON.stringify(data) }),
};
