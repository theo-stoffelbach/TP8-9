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
};
