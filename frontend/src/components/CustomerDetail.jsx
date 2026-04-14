import { useEffect, useState } from "react";
import { api } from "../api";
import AddressForm from "./AddressForm";

const s = {
  backBtn: {
    padding: "7px 14px",
    background: "#f0f0f0",
    color: "#333",
    borderRadius: 6,
    fontSize: "0.85rem",
    marginBottom: 20,
  },
  card: {
    background: "#fff",
    borderRadius: 10,
    padding: 20,
    boxShadow: "0 1px 4px rgba(0,0,0,.07)",
    marginBottom: 16,
  },
  row: { display: "flex", justifyContent: "space-between", alignItems: "flex-start" },
  name: { fontSize: "1.3rem", fontWeight: 700 },
  badge: (active) => ({
    fontSize: "0.75rem",
    padding: "4px 10px",
    borderRadius: 20,
    background: active ? "#d1fae5" : "#fee2e2",
    color: active ? "#065f46" : "#991b1b",
    fontWeight: 600,
  }),
  field: { marginTop: 10, fontSize: "0.875rem", color: "#555" },
  editBtn: {
    padding: "5px 12px",
    background: "#f0f0f0",
    color: "#333",
    borderRadius: 6,
    fontSize: "0.8rem",
    marginTop: 14,
  },
  sectionTitle: {
    fontWeight: 700,
    marginBottom: 12,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  addBtn: { padding: "6px 12px", background: "#1a1a1a", color: "#fff", borderRadius: 6, fontSize: "0.8rem" },
  addrCard: (isDefault) => ({
    background: isDefault ? "#f8f8f8" : "#fff",
    border: isDefault ? "1px solid #ddd" : "1px solid #eee",
    borderRadius: 8,
    padding: "12px 14px",
    marginBottom: 8,
    fontSize: "0.875rem",
  }),
  addrDefault: { fontSize: "0.72rem", fontWeight: 700, color: "#555", marginBottom: 4, textTransform: "uppercase" },
  addrActions: { display: "flex", gap: 6, marginTop: 8 },
  addrEditBtn: { padding: "4px 10px", background: "#f0f0f0", color: "#333", borderRadius: 5, fontSize: "0.78rem" },
  empty: { color: "#aaa", fontSize: "0.875rem" },
  error: { color: "#dc2626", padding: 12, background: "#fef2f2", borderRadius: 8 },

  // inline edit form
  form: { marginTop: 14, display: "flex", flexDirection: "column", gap: 10 },
  inputGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" },
  fieldGroup: { display: "flex", flexDirection: "column", gap: 4 },
  label: { fontSize: "0.75rem", fontWeight: 600, color: "#666" },
  input: { padding: "8px 10px", border: "1px solid #ddd", borderRadius: 6, fontSize: "0.875rem", outline: "none" },
  formRow: { display: "flex", gap: 8 },
  saveBtn: { flex: 1, padding: "8px", background: "#1a1a1a", color: "#fff", borderRadius: 6, fontWeight: 600 },
  cancelFormBtn: { padding: "8px 14px", background: "#f0f0f0", color: "#333", borderRadius: 6 },
  formError: { color: "#dc2626", fontSize: "0.82rem" },
};

function CustomerEditForm({ customer, onSaved, onCancel }) {
  const [form, setForm] = useState({
    first_name: customer.first_name,
    last_name: customer.last_name,
    email: customer.email,
    phone: customer.phone,
    is_active: customer.is_active,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateCustomer(customer.id, form);
      onSaved(updated);
    } catch (err) {
      const detail = err.body
        ? Object.entries(err.body).map(([k, v]) => `${k} : ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ")
        : err.message;
      setError(detail);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form style={s.form} onSubmit={handleSubmit}>
      {error && <div style={s.formError}>{error}</div>}
      <div style={s.inputGrid}>
        <div style={s.fieldGroup}>
          <label style={s.label}>Prénom</label>
          <input style={s.input} required value={form.first_name} onChange={set("first_name")} />
        </div>
        <div style={s.fieldGroup}>
          <label style={s.label}>Nom</label>
          <input style={s.input} required value={form.last_name} onChange={set("last_name")} />
        </div>
      </div>
      <div style={s.fieldGroup}>
        <label style={s.label}>Email</label>
        <input style={s.input} type="email" required value={form.email} onChange={set("email")} />
      </div>
      <div style={s.fieldGroup}>
        <label style={s.label}>Téléphone</label>
        <input style={s.input} required value={form.phone} onChange={set("phone")} />
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.85rem" }}>
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
        />
        Client actif
      </label>
      <div style={s.formRow}>
        <button type="button" style={s.cancelFormBtn} onClick={onCancel}>Annuler</button>
        <button type="submit" style={s.saveBtn} disabled={saving}>{saving ? "Enregistrement…" : "Enregistrer"}</button>
      </div>
    </form>
  );
}

function AddressEditForm({ customerId, address, onSaved, onCancel }) {
  const [form, setForm] = useState({
    street: address.street,
    postal_code: address.postal_code,
    city: address.city,
    country: address.country,
    is_default: address.is_default,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await api.updateAddress(customerId, address.id, form);
      onSaved(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form style={{ ...s.form, marginTop: 8 }} onSubmit={handleSubmit}>
      {error && <div style={s.formError}>{error}</div>}
      <div style={s.fieldGroup}>
        <label style={s.label}>Rue</label>
        <input style={s.input} required value={form.street} onChange={set("street")} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: "0 10px" }}>
        <div style={s.fieldGroup}>
          <label style={s.label}>Code postal</label>
          <input style={s.input} required value={form.postal_code} onChange={set("postal_code")} />
        </div>
        <div style={s.fieldGroup}>
          <label style={s.label}>Ville</label>
          <input style={s.input} required value={form.city} onChange={set("city")} />
        </div>
      </div>
      <div style={s.fieldGroup}>
        <label style={s.label}>Pays</label>
        <input style={s.input} value={form.country} onChange={set("country")} />
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.85rem" }}>
        <input
          type="checkbox"
          checked={form.is_default}
          onChange={(e) => setForm((f) => ({ ...f, is_default: e.target.checked }))}
        />
        Adresse principale
      </label>
      <div style={s.formRow}>
        <button type="button" style={s.cancelFormBtn} onClick={onCancel}>Annuler</button>
        <button type="submit" style={s.saveBtn} disabled={saving}>{saving ? "Enregistrement…" : "Enregistrer"}</button>
      </div>
    </form>
  );
}

export default function CustomerDetail({ id, onBack }) {
  const [customer, setCustomer] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingCustomer, setEditingCustomer] = useState(false);
  const [editingAddressId, setEditingAddressId] = useState(null);
  const [showAddressForm, setShowAddressForm] = useState(false);

  function loadAddresses() {
    api.getAddresses(id).then(setAddresses).catch(() => {});
  }

  useEffect(() => {
    Promise.all([api.getCustomer(id), api.getAddresses(id)])
      .then(([c, a]) => { setCustomer(c); setAddresses(a); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  function onCustomerSaved(updated) {
    setCustomer(updated);
    setEditingCustomer(false);
  }

  function onAddressSaved(updated) {
    setAddresses((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
    setEditingAddressId(null);
  }

  if (loading) return <p style={{ color: "#999" }}>Chargement…</p>;
  if (error) return <p style={s.error}>⚠ {error}</p>;
  if (!customer) return null;

  return (
    <div>
      <button style={s.backBtn} onClick={onBack}>← Retour</button>

      <div style={s.card}>
        <div style={s.row}>
          <div style={s.name}>{customer.first_name} {customer.last_name}</div>
          <span style={s.badge(customer.is_active)}>{customer.is_active ? "Actif" : "Inactif"}</span>
        </div>

        {!editingCustomer ? (
          <>
            <div style={s.field}><strong>Email :</strong> {customer.email}</div>
            <div style={s.field}><strong>Téléphone :</strong> {customer.phone}</div>
            <div style={s.field}><strong>ID :</strong> #{customer.id}</div>
            <button style={s.editBtn} onClick={() => setEditingCustomer(true)}>Modifier</button>
          </>
        ) : (
          <CustomerEditForm
            customer={customer}
            onSaved={onCustomerSaved}
            onCancel={() => setEditingCustomer(false)}
          />
        )}
      </div>

      <div style={s.card}>
        <div style={s.sectionTitle}>
          Adresses de livraison
          <button style={s.addBtn} onClick={() => { setShowAddressForm((v) => !v); setEditingAddressId(null); }}>
            {showAddressForm ? "Annuler" : "+ Ajouter"}
          </button>
        </div>

        {showAddressForm && (
          <AddressForm
            customerId={id}
            onCreated={() => { setShowAddressForm(false); loadAddresses(); }}
            onCancel={() => setShowAddressForm(false)}
          />
        )}

        {addresses.length === 0 && !showAddressForm ? (
          <p style={s.empty}>Aucune adresse enregistrée.</p>
        ) : (
          addresses.map((a) => (
            <div key={a.id} style={s.addrCard(a.is_default)}>
              {editingAddressId === a.id ? (
                <AddressEditForm
                  customerId={id}
                  address={a}
                  onSaved={onAddressSaved}
                  onCancel={() => setEditingAddressId(null)}
                />
              ) : (
                <>
                  {a.is_default && <div style={s.addrDefault}>★ Adresse principale</div>}
                  <div>{a.street}</div>
                  <div>{a.postal_code} {a.city}, {a.country}</div>
                  <div style={s.addrActions}>
                    <button
                      style={s.addrEditBtn}
                      onClick={() => { setEditingAddressId(a.id); setShowAddressForm(false); }}
                    >
                      Modifier
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
