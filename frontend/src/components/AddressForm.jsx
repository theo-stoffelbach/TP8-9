import { useState } from "react";
import { api } from "../api";

const s = {
  root: {
    background: "#f8f8f8",
    border: "1px solid #e5e5e5",
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  title: { fontWeight: 600, fontSize: "0.875rem", marginBottom: 12 },
  field: { display: "flex", flexDirection: "column", gap: 4, marginBottom: 10 },
  label: { fontSize: "0.75rem", fontWeight: 600, color: "#666" },
  input: {
    padding: "8px 10px",
    border: "1px solid #ddd",
    borderRadius: 6,
    fontSize: "0.875rem",
    outline: "none",
    background: "#fff",
  },
  row: { display: "flex", gap: 8, marginTop: 4 },
  submitBtn: { flex: 1, padding: "8px", background: "#1a1a1a", color: "#fff", borderRadius: 6 },
  cancelBtn: { padding: "8px 12px", background: "#e5e5e5", color: "#333", borderRadius: 6 },
  checkRow: { display: "flex", alignItems: "center", gap: 8, fontSize: "0.85rem", margin: "8px 0" },
  error: { color: "#dc2626", fontSize: "0.82rem", marginBottom: 8 },
};

const EMPTY = { street: "", postal_code: "", city: "", country: "France", is_default: false };

export default function AddressForm({ customerId, onCreated, onCancel, cancelLabel = "Annuler" }) {
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createAddress(customerId, form);
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={s.root}>
      <div style={s.title}>Nouvelle adresse</div>
      {error && <div style={s.error}>{error}</div>}
      <form onSubmit={handleSubmit}>
        <div style={s.field}>
          <label style={s.label}>Rue *</label>
          <input style={s.input} required value={form.street} onChange={set("street")} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: "0 10px" }}>
          <div style={s.field}>
            <label style={s.label}>Code postal *</label>
            <input style={s.input} required value={form.postal_code} onChange={set("postal_code")} />
          </div>
          <div style={s.field}>
            <label style={s.label}>Ville *</label>
            <input style={s.input} required value={form.city} onChange={set("city")} />
          </div>
        </div>
        <div style={s.field}>
          <label style={s.label}>Pays</label>
          <input style={s.input} value={form.country} onChange={set("country")} />
        </div>
        <label style={s.checkRow}>
          <input
            type="checkbox"
            checked={form.is_default}
            onChange={(e) => setForm((f) => ({ ...f, is_default: e.target.checked }))}
          />
          Adresse principale
        </label>
        <div style={s.row}>
          <button type="button" style={s.cancelBtn} onClick={onCancel}>{cancelLabel}</button>
          <button type="submit" style={s.submitBtn} disabled={submitting}>
            {submitting ? "Ajout…" : "Ajouter l'adresse"}
          </button>
        </div>
      </form>
    </div>
  );
}
