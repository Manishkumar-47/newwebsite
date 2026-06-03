import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/newwebsite/",
  plugins: [react()],
  server: {
    port: 5173,
  },
});

