// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Build timestamp → sitemap <lastmod> (updates every deploy).
const buildDate = new Date().toISOString();

export default defineConfig({
  site: 'https://brain-exposome.mattye.dev',
  output: 'static',
  integrations: [
    sitemap({
      serialize(item) {
        item.lastmod = buildDate;
        return item;
      },
    }),
  ],
});
