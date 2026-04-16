import { useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from "react-router-dom";
import CustomerDetail from "./components/CustomerDetail";
import CustomerForm from "./components/CustomerForm";
import CustomerList from "./components/CustomerList";
import CatalogList from "./components/CatalogList";
import OrderList from "./components/OrderList";
import OrderCreate from "./components/OrderCreate";

const s = {
  header: {
    background: "#1a1a1a",
    color: "#fff",
    padding: "0 24px",
    height: 56,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  logo: { fontWeight: 800, fontSize: "1.1rem", letterSpacing: "-0.02em", cursor: "pointer", color: "#fff", textDecoration: "none" },
  nav: { display: "flex", gap: 4, alignItems: "center" },
  main: { padding: 24, maxWidth: 860, margin: "0 auto" },
};

const navLinkStyle = ({ isActive }) => ({
  padding: "6px 14px",
  borderRadius: 6,
  fontWeight: 600,
  fontSize: "0.82rem",
  cursor: "pointer",
  background: isActive ? "#fff" : "transparent",
  color: isActive ? "#1a1a1a" : "rgba(255,255,255,0.65)",
  transition: "background 0.15s, color 0.15s",
  textDecoration: "none",
});

const actionBtnStyle = {
  padding: "7px 14px",
  background: "#fff",
  color: "#1a1a1a",
  borderRadius: 6,
  fontWeight: 600,
  fontSize: "0.8rem",
  cursor: "pointer",
  border: "none",
};

function CustomersPage() {
  const [selectedId, setSelectedId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [refresh, setRefresh] = useState(0);

  function onCreated() {
    setShowForm(false);
    setRefresh((k) => k + 1);
  }

  if (showForm) {
    return <CustomerForm onCreated={onCreated} onCancel={() => setShowForm(false)} />;
  }
  if (selectedId) {
    return <CustomerDetail id={selectedId} onBack={() => setSelectedId(null)} />;
  }
  return (
    <>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
        <button style={actionBtnStyle} onClick={() => setShowForm(true)}>+ Nouveau client</button>
      </div>
      <CustomerList key={refresh} onSelect={setSelectedId} />
    </>
  );
}

function OrdersPage() {
  const [showForm, setShowForm] = useState(false);
  const [refresh, setRefresh] = useState(0);

  function onCreated() {
    setShowForm(false);
    setRefresh((k) => k + 1);
  }

  if (showForm) {
    return <OrderCreate onCreated={onCreated} onCancel={() => setShowForm(false)} />;
  }
  return (
    <>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 16 }}>
        <button style={actionBtnStyle} onClick={() => setShowForm(true)}>+ Nouvelle commande</button>
      </div>
      <OrderList key={refresh} refreshKey={refresh} />
    </>
  );
}

function Layout() {
  const navigate = useNavigate();

  return (
    <>
      <header style={s.header}>
        <a style={s.logo} onClick={() => navigate("/customers")} role="button" tabIndex={0}>
          Zalandouille
        </a>
        <nav style={s.nav}>
          <NavLink to="/customers" style={navLinkStyle}>Clients</NavLink>
          <NavLink to="/catalog" style={navLinkStyle}>Catalogue</NavLink>
          <NavLink to="/orders" style={navLinkStyle}>Commandes</NavLink>
        </nav>
      </header>

      <main style={s.main}>
        <Routes>
          <Route path="/" element={<Navigate to="/customers" replace />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="/catalog" element={<CatalogList />} />
          <Route path="/orders" element={<OrdersPage />} />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
