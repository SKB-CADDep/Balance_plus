import {TanStackRouterVite} from "@tanstack/router-vite-plugin"
import react from "@vitejs/plugin-react-swc"
import {defineConfig} from "vitest/config"

export default defineConfig({
    plugins: [react(), TanStackRouterVite()],
    test: {
        include: ["src/**/*.test.{ts,tsx}"],
    },
    server: {
        port: 3001,
        proxy: {
            '/api': {
                target: 'http://localhost:8010',
                changeOrigin: true,
                secure: false,
            }
        }
    },
});
