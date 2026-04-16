import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    historyApiFallback: true,
    port: 5173,
    proxy: {
      "/api/customers": {
        target: process.env.VITE_CUSTOMER_URL || "http://web:8000",
        changeOrigin: true,
      },
      "/api/products": {
        target: process.env.VITE_CATALOG_URL || "http://web:8001",
        changeOrigin: true,
      },
      "/api/orders": {
        target: process.env.VITE_ORDER_URL || "http://web:8002",
        changeOrigin: true,
      },
    },
  },
});
