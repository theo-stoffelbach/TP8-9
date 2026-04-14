import { useState } from "react";
import CustomerDetail from "./components/CustomerDetail";
import CustomerForm from "./components/CustomerForm";
import CustomerList from "./components/CustomerList";
import CatalogList from "./components/CatalogList";
import OrderList from "./components/OrderList";
import OrderCreate from "./components/OrderCreate";

const TABS = ["clients", "catalog", "orders"];
const TAB_LABEL = { clients: "Clients", catalog: "Catalogue", orders: "Commandes" };

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
  logo: { fontWeight: 800, fontSize: "1.1rem", letterSpacing: "-0.02em", cursor: "pointer" },
  nav: { display: "flex", gap: 4, alignItems: "center" },
  tab: (active) => ({
    padding: "6px 14px",
    borderRadius: 6,
    fontWeight: 600,
    fontSize: "0.82rem",
    cursor: "pointer",
    background: active ? "#fff" : "transparent",
    color: active ? "#1a1a1a" : "rgba(255,255,255,0.65)",
    transition: "background 0.15s, color 0.15s",
  }),
  actionBtn: {
    padding: "7px 14px",
    background: "#fff",
    color: "#1a1a1a",
    borderRadius: 6,
    fontWeight: 600,
    fontSize: "0.8rem",
    cursor: "pointer",
  },
  main: { padding: 24, maxWidth: 860, margin: "0 auto" },
};

export default function App() {
  const [tab, setTab] = useState("clients");

  // Clients state
  const [selectedId, setSelectedId] = useState(null);
  const [showCustomerForm, setShowCustomerForm] = useState(false);
  const [clientRefresh, setClientRefresh] = useState(0);

  // Orders state
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [orderRefresh, setOrderRefresh] = useState(0);

  function switchTab(t) {
    setTab(t);
    setSelectedId(null);
    setShowCustomerForm(false);
    setShowOrderForm(false);
  }

  function onCustomerCreated() {
    setShowCustomerForm(false);
    setClientRefresh((k) => k + 1);
  }

  function onOrderCreated() {
    setShowOrderForm(false);
    setOrderRefresh((k) => k + 1);
  }

  function renderActionBtn() {
    if (tab === "clients" && !showCustomerForm && !selectedId) {
      return (
        <button style={s.actionBtn} onClick={() => { setSelectedId(null); setShowCustomerForm(true); }}>
          + Nouveau client
        </button>
      );
    }
    if (tab === "orders" && !showOrderForm) {
      return (
        <button style={s.actionBtn} onClick={() => setShowOrderForm(true)}>
          + Nouvelle commande
        </button>
      );
    }
    return null;
  }

  return (
    <>
      <header style={s.header}>
        <span style={s.logo} onClick={() => switchTab("clients")} role="button" tabIndex={0}>
          Zalandouille
        </span>
        <nav style={s.nav}>
          {TABS.map((t) => (
            <button key={t} style={s.tab(tab === t)} onClick={() => switchTab(t)}>
              {TAB_LABEL[t]}
            </button>
          ))}
        </nav>
        {renderActionBtn()}
      </header>

      <main style={s.main}>
        {tab === "clients" && (
          showCustomerForm ? (
            <CustomerForm onCreated={onCustomerCreated} onCancel={() => setShowCustomerForm(false)} />
          ) : selectedId ? (
            <CustomerDetail id={selectedId} onBack={() => setSelectedId(null)} />
          ) : (
            <CustomerList key={clientRefresh} onSelect={setSelectedId} />
          )
        )}

        {tab === "catalog" && <CatalogList />}

        {tab === "orders" && (
          showOrderForm ? (
            <OrderCreate onCreated={onOrderCreated} onCancel={() => setShowOrderForm(false)} />
          ) : (
            <OrderList key={orderRefresh} refreshKey={orderRefresh} />
          )
        )}
      </main>
    </>
  );
}
