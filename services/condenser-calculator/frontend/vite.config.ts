import {TanStackRouterVite} from "@tanstack/router-vite-plugin"
import react from "@vitejs/plugin-react-swc"
import {defineConfig} from "vite"

export default defineConfig({
    plugins: [react(), TanStackRouterVite()],
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
