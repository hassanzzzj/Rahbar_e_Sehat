/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_MAP_TILE_URL?: string;
  readonly VITE_MAP_DEFAULT_CENTER?: string;
  readonly VITE_MAP_DEFAULT_ZOOM?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_ENABLE_VOICE_INPUT?: string;
  readonly VITE_ENABLE_URDU_UI?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
