// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://brain-exposome.mattye.dev',
  output: 'static',
  integrations: [sitemap()],
});
