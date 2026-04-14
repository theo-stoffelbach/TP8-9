import { useEffect, useState } from "react";
import { api } from "../api";

const s = {
  root: { display: "flex", flexDirection: "column", gap: 20 },
  section: {
    background: "#fff",
    border: "1px solid #eee",
    borderRadius: 12,
    padding: 20,
    boxShadow: "0 1px 3px rgba(0,0,0,.05)",
  },
  title: { fontWeight: 700, fontSize: "0.95rem", marginBottom: 14 },
  row: { display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" },
  label: { display: "flex", flexDirection: "column", gap: 4, flex: 1, minWidth: 120 },
  labelText: { fontSize: "0.78rem", color: "#666", fontWeight: 600 },
  input: {
    padding: "9px 12px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: "0.9rem",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  },
  select: {
    padding: "9px 12px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: "0.9rem",
    outline: "none",
    background: "#fff",
    flex: 2,
    minWidth: 160,
  },
  addBtn: {
    padding: "9px 14px",
    background: "#1a1a1a",
    color: "#fff",
    borderRadius: 8,
    fontSize: "0.85rem",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  removeBtn: {
    padding: "6px 10px",
    background: "#fee2e2",
    color: "#991b1b",
    borderRadius: 6,
    fontSize: "0.8rem",
    cursor: "pointer",
  },
  itemRow: {
    display: "flex",
    gap: 10,
    alignItems: "center",
    padding: "10px 0",
    borderBottom: "1px solid #f4f4f4",
  },
  itemName: { flex: 1, fontSize: "0.88rem" },
  itemQty: { padding: "6px 10px", border: "1px solid #ddd", borderRadius: 6, width: 70, fontSize: "0.9rem" },
  itemPrice: { fontSize: "0.82rem", color: "#666", minWidth: 60, textAlign: "right" },
  actions: { display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 4 },
  cancelBtn: {
    padding: "10px 18px",
    background: "#f0f0f0",
    color: "#555",
    borderRadius: 8,
    fontWeight: 600,
    fontSize: "0.88rem",
    cursor: "pointer",
  },
  submitBtn: (disabled) => ({
    padding: "10px 20px",
    background: disabled ? "#ccc" : "#1a1a1a",
    color: "#fff",
    borderRadius: 8,
    fontWeight: 600,
    fontSize: "0.88rem",
    cursor: disabled ? "default" : "pointer",
  }),
  error: { color: "#dc2626", padding: 10, background: "#fef2f2", borderRadius: 8, fontSize: "0.85rem" },
  total: { fontWeight: 800, fontSize: "1.05rem", textAlign: "right", marginTop: 8 },
};

export default function OrderCreate({ onCreated, onCancel }) {
  const [customerId, setCustomerId] = useState("");
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [lines, setLines] = useState([]);
  const [newProductId, setNewProductId] = useState("");
  const [newQty, setNewQty] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getCustomers().then((data) => setCustomers(Array.isArray(data) ? data : data.results ?? [])).catch(() => {});
    api.getProducts().then((data) => setProducts(Array.isArray(data) ? data : data.results ?? [])).catch(() => {});
  }, []);

  function addLine() {
    if (!newProductId) return;
    const product = products.find((p) => String(p.id) === String(newProductId));
    if (!product) return;
    setLines((prev) => {
      const existing = prev.findIndex((l) => l.product_id === product.id);
      if (existing >= 0) {
        return prev.map((l, i) => i === existing ? { ...l, quantity: l.quantity + Number(newQty) } : l);
      }
      return [...prev, { product_id: product.id, product_name: product.name, unit_price: parseFloat(product.price), quantity: Number(newQty) }];
    });
    setNewProductId("");
    setNewQty(1);
  }

  function removeLine(idx) {
    setLines((prev) => prev.filter((_, i) => i !== idx));
  }

  function updateQty(idx, val) {
    const q = Math.max(1, Number(val));
    setLines((prev) => prev.map((l, i) => i === idx ? { ...l, quantity: q } : l));
  }

  const total = lines.reduce((sum, l) => sum + l.unit_price * l.quantity, 0);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!customerId || lines.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.createOrder({
        customer_id: Number(customerId),
        items: lines.map(({ product_id, quantity }) => ({ product_id, quantity })),
      });
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const canSubmit = customerId && lines.length > 0 && !submitting;

  return (
    <form style={s.root} onSubmit={handleSubmit}>
      <div style={s.section}>
        <div style={s.title}>Informations client</div>
        <label style={s.label}>
          <span style={s.labelText}>Client</span>
          <select
            style={s.select}
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            required
          >
            <option value="">Sélectionner un client…</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.first_name} {c.last_name} — {c.email}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div style={s.section}>
        <div style={s.title}>Produits</div>
        <div style={s.row}>
          <select
            style={s.select}
            value={newProductId}
            onChange={(e) => setNewProductId(e.target.value)}
          >
            <option value="">Sélectionner un produit…</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {parseFloat(p.price).toFixed(2)} €
              </option>
            ))}
          </select>
          <label style={{ ...s.label, flex: "0 0 80px" }}>
            <span style={s.labelText}>Qté</span>
            <input
              style={s.input}
              type="number"
              min={1}
              value={newQty}
              onChange={(e) => setNewQty(e.target.value)}
            />
          </label>
          <button type="button" style={s.addBtn} onClick={addLine}>+ Ajouter</button>
        </div>

        {lines.length > 0 && (
          <div style={{ marginTop: 14 }}>
            {lines.map((l, i) => (
              <div key={i} style={s.itemRow}>
                <span style={s.itemName}>{l.product_name}</span>
                <input
                  style={s.itemQty}
                  type="number"
                  min={1}
                  value={l.quantity}
                  onChange={(e) => updateQty(i, e.target.value)}
                />
                <span style={s.itemPrice}>{(l.unit_price * l.quantity).toFixed(2)} €</span>
                <button type="button" style={s.removeBtn} onClick={() => removeLine(i)}>✕</button>
              </div>
            ))}
            <div style={s.total}>Total estimé : {total.toFixed(2)} €</div>
          </div>
        )}
      </div>

      {error && <p style={s.error}>⚠ {error}</p>}

      <div style={s.actions}>
        <button type="button" style={s.cancelBtn} onClick={onCancel}>Annuler</button>
        <button type="submit" style={s.submitBtn(!canSubmit)} disabled={!canSubmit}>
          {submitting ? "Envoi…" : "Créer la commande"}
        </button>
      </div>
    </form>
  );
}
