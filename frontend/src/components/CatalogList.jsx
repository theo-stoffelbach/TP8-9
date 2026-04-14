import { useEffect, useState } from "react";
import { api } from "../api";

const s = {
  root: { display: "flex", flexDirection: "column", gap: 16 },
  toolbar: { display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" },
  search: {
    flex: 1,
    minWidth: 160,
    padding: "10px 14px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: "0.9rem",
    outline: "none",
  },
  select: {
    padding: "10px 14px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: "0.9rem",
    outline: "none",
    background: "#fff",
  },
  searchBtn: {
    padding: "10px 16px",
    background: "#1a1a1a",
    color: "#fff",
    borderRadius: 8,
    fontSize: "0.85rem",
    cursor: "pointer",
  },
  clearBtn: {
    padding: "10px 12px",
    background: "#f0f0f0",
    color: "#555",
    borderRadius: 8,
    fontSize: "0.85rem",
    cursor: "pointer",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: 16,
  },
  card: {
    background: "#fff",
    border: "1px solid #eee",
    borderRadius: 12,
    padding: 16,
    boxShadow: "0 1px 3px rgba(0,0,0,.06)",
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  name: { fontWeight: 700, fontSize: "0.95rem" },
  category: { fontSize: "0.75rem", color: "#888", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" },
  desc: { fontSize: "0.82rem", color: "#555", flex: 1 },
  footer: { display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 },
  price: { fontWeight: 800, fontSize: "1.05rem", color: "#1a1a1a" },
  stock: (n) => ({
    fontSize: "0.75rem",
    padding: "2px 8px",
    borderRadius: 20,
    background: n > 0 ? "#d1fae5" : "#fee2e2",
    color: n > 0 ? "#065f46" : "#991b1b",
    fontWeight: 600,
  }),
  empty: { color: "#999", textAlign: "center", padding: 48 },
  error: { color: "#dc2626", padding: 12, background: "#fef2f2", borderRadius: 8 },
};

export default function CatalogList() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [appliedCategory, setAppliedCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {});
  }, []);

  function load(search = "", categoryId = "") {
    setLoading(true);
    setError(null);
    api.getProducts({ search, categoryId })
      .then((data) => setProducts(Array.isArray(data) ? data : data.results ?? []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  function handleSearch(e) {
    e.preventDefault();
    setAppliedSearch(search);
    setAppliedCategory(categoryId);
    load(search, categoryId);
  }

  function handleClear() {
    setSearch("");
    setCategoryId("");
    setAppliedSearch("");
    setAppliedCategory("");
    load();
  }

  const isDirty = appliedSearch || appliedCategory;

  return (
    <div style={s.root}>
      <form style={s.toolbar} onSubmit={handleSearch}>
        <input
          style={s.search}
          placeholder="Rechercher un produit…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select style={s.select} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">Toutes catégories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <button type="submit" style={s.searchBtn}>Filtrer</button>
        {isDirty && (
          <button type="button" style={s.clearBtn} onClick={handleClear}>✕ Réinit.</button>
        )}
      </form>

      {loading ? (
        <p style={s.empty}>Chargement…</p>
      ) : error ? (
        <p style={s.error}>⚠ {error}</p>
      ) : products.length === 0 ? (
        <p style={s.empty}>Aucun produit trouvé.</p>
      ) : (
        <div style={s.grid}>
          {products.map((p) => (
            <div key={p.id} style={s.card}>
              <div style={s.category}>{p.category?.name ?? "—"}</div>
              <div style={s.name}>{p.name}</div>
              {p.description && <div style={s.desc}>{p.description}</div>}
              <div style={s.footer}>
                <span style={s.price}>{parseFloat(p.price).toFixed(2)} €</span>
                <span style={s.stock(p.stock)}>
                  {p.stock > 0 ? `Stock: ${p.stock}` : "Rupture"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
