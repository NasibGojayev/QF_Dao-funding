import { defineConfig } from 'vite';
import { compression } from 'vite-plugin-compression2';

export default defineConfig({
    build: {
        // Enable minification
        minify: 'terser',
        terserOptions: {
            compress: {
                drop_console: true,
                drop_debugger: true,
            },
        },
        // Optimize chunk splitting
        rollupOptions: {
            output: {
                manualChunks: {
                    // Separate Three.js into its own chunk for better caching
                    three: ['three'],
                },
            },
        },
        // Optimize CSS
        cssCodeSplit: true,
        // Target modern browsers for smaller bundles
        target: 'es2015',
        // Increase chunk size warning limit for Three.js
        chunkSizeWarningLimit: 1000,
    },
    // Enable compression in preview mode
    plugins: [],
    server: {
        // Enable compression for dev server
        compress: true,
    },
});
