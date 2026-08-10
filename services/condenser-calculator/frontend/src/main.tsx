import { ChakraProvider, ColorModeScript } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import ReactDOM from "react-dom/client";
import { routeTree } from "./routeTree.gen";

import { StrictMode } from "react";
import { OpenAPI } from "./client";
import theme from "./theme";

const getApiBaseUrl = (): string => {
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
    }
    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.hostname}:8010`;
    }
    return "http://localhost:8010";
};

OpenAPI.BASE = getApiBaseUrl();

const queryClient = new QueryClient();

const router = createRouter({
    routeTree,
});

declare module "@tanstack/react-router" {
}

const initialColorMode = theme.config.initialColorMode;

ReactDOM.createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <ColorModeScript initialColorMode={initialColorMode} />

        <ChakraProvider theme={theme}>
            <QueryClientProvider client={queryClient}>
                <RouterProvider router={router} />
            </QueryClientProvider>
        </ChakraProvider>

    </StrictMode>,
);