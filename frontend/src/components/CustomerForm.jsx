import { useState } from "react";
import { api } from "../api";
import AddressForm from "./AddressForm";

const s = {
  card: {
    background: "#fff",
    borderRadius: 10,
    padding: 24,
    boxShadow: "0 1px 4px rgba(0,0,0,.07)",
    maxWidth: 480,
  },
  title: { fontWeight: 700, fontSize: "1.05rem", marginBottom: 20 },
  field: { display: "flex", flexDirection: "column", gap: 5, marginBottom: 14 },
  label: { fontSize: "0.8rem", fontWeight: 600, color: "#555" },
  input: {
    padding: "9px 12px",
    border: "1px solid #ddd",
    borderRadius: 7,
    fontSize: "0.9rem",
    outline: "none",
  },
  row: { display: "flex", gap: 10, marginTop: 8 },
  submitBtn: { flex: 1, padding: "10px", background: "#1a1a1a", color: "#fff", borderRadius: 8, fontWeight: 600 },
  cancelBtn: { padding: "10px 16px", background: "#f0f0f0", color: "#333", borderRadius: 8 },
  skipBtn: { padding: "10px 16px", background: "#f0f0f0", color: "#333", borderRadius: 8 },
  error: { color: "#dc2626", fontSize: "0.85rem", padding: "8px 12px", background: "#fef2f2", borderRadius: 7, marginBottom: 12 },
  success: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 12px",
    background: "#d1fae5",
    borderRadius: 7,
    fontSize: "0.85rem",
    color: "#065f46",
    fontWeight: 600,
    marginBottom: 16,
  },
  divider: { borderTop: "1px solid #f0f0f0", margin: "20px 0" },
};

const EMPTY = { first_name: "", last_name: "", email: "", phone: "" };

export default function CustomerForm({ onCreated, onCancel }) {
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [createdCustomer, setCreatedCustomer] = useState(null);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const customer = await api.createCustomer(form);
      setCreatedCustomer(customer);
    } catch (err) {
      const detail = err.body
        ? Object.entries(err.body).map(([k, v]) => `${k} : ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ")
        : err.message;
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  }

  if (createdCustomer) {
    return (
      <div style={s.card}>
        <div style={s.success}>
          ✓ {createdCustomer.first_name} {createdCustomer.last_name} créé(e)
        </div>
        <div style={{ fontWeight: 700, marginBottom: 16 }}>Ajouter une adresse de livraison</div>
        <AddressForm
          customerId={createdCustomer.id}
          onCreated={onCreated}
          onCancel={onCreated}
          cancelLabel="Passer"
        />
      </div>
    );
  }

  return (
    <div style={s.card}>
      <div style={s.title}>Nouveau client</div>
      {error && <div style={s.error}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" }}>
          <div style={s.field}>
            <label style={s.label}>Prénom *</label>
            <input style={s.input} required value={form.first_name} onChange={set("first_name")} />
          </div>
          <div style={s.field}>
            <label style={s.label}>Nom *</label>
            <input style={s.input} required value={form.last_name} onChange={set("last_name")} />
          </div>
        </div>
        <div style={s.field}>
          <label style={s.label}>Email *</label>
          <input style={s.input} type="email" required value={form.email} onChange={set("email")} />
        </div>
        <div style={s.field}>
          <label style={s.label}>Téléphone *</label>
          <input style={s.input} required value={form.phone} onChange={set("phone")} />
        </div>
        <div style={s.row}>
          <button type="button" style={s.cancelBtn} onClick={onCancel}>Annuler</button>
          <button type="submit" style={s.submitBtn} disabled={submitting}>
            {submitting ? "Création…" : "Créer le client"}
          </button>
        </div>
      </form>
    </div>
  );
}
