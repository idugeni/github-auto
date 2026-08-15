# Frontend

Tauri + React desktop application for github-auto.

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Desktop | Tauri | 2.2 |
| UI | React | 19.1 |
| Styling | Tailwind CSS | 4.1 |
| Components | shadcn/ui | Radix + CVA |
| Build | Vite | 6.4 |
| Language | TypeScript | 5.8 |
| Backend | Rust | 2021 edition |

## Development

```bash
# Install dependencies
npm install

# Dev server (browser only)
npm run dev

# Dev server (Tauri desktop)
npm run tauri dev

# Type check
npx tsc --noEmit

# Build
npm run build

# Production build
npm run tauri build
```

## Project Structure

```
frontend/
├── src-tauri/                 # Rust backend
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── src/
│       ├── main.rs
│       └── lib.rs             # Tauri commands
├── src/                       # React frontend
│   ├── main.tsx               # Entry point
│   ├── App.tsx                # Root + router
│   ├── globals.css            # Tailwind + glassmorphism tokens
│   ├── components/
│   │   ├── layout/
│   │   │   ├── shell.tsx      # Main layout
│   │   │   ├── sidebar.tsx    # Navigation
│   │   │   └── header.tsx     # Titlebar
│   │   └── ui/                # shadcn/ui components
│   ├── features/              # Page modules
│   │   ├── dashboard/
│   │   ├── accounts/
│   │   ├── register/
│   │   ├── proxy/
│   │   ├── email/
│   │   ├── logs/
│   │   ├── export/
│   │   └── settings/
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utilities + Tauri IPC
│   └── types/                 # TypeScript types
├── package.json
├── vite.config.ts
├── tsconfig.json
└── components.json            # shadcn/ui config
```

## Design System

### Glassmorphism

```css
/* Light mode */
--glass-bg: rgba(255, 255, 255, 0.65);
--glass-border: rgba(255, 255, 255, 0.5);
--mica-bg: rgba(243, 243, 243, 0.72);

/* Dark mode */
--glass-bg: rgba(44, 44, 44, 0.65);
--glass-border: rgba(255, 255, 255, 0.08);
--mica-bg: rgba(32, 32, 32, 0.80);
```

### Utility Classes

- `glass` — Full glass effect
- `glass-card` — Glass card
- `glass-card-hover` — Glass card with hover
- `sidebar-glass` — Sidebar glass
- `titlebar` — Titlebar glass
- `mica` — Mica background

## Adding Pages

1. Create `src/features/{page}/page.tsx`
2. Export: `export function {Page}Page()`
3. Add to `src/App.tsx` router
4. Add nav item in `src/components/layout/sidebar.tsx`
5. Add title in `src/components/layout/shell.tsx`

## Adding Components

```tsx
import { cn } from "@/lib/utils";

interface MyComponentProps {
  className?: string;
}

export function MyComponent({ className }: MyComponentProps) {
  return (
    <div className={cn("glass-card", className)}>
      {/* Content */}
    </div>
  );
}
```

## Tauri Commands

```typescript
import { invoke } from "@tauri-apps/api/core";

// Call Rust command
const accounts = await invoke<Account[]>("get_accounts");

// With args
await invoke("register_accounts", { count: 5 });
```

## Environment

| Variable | Description |
|----------|-------------|
| `TAURI_DEV_HOST` | Dev server host |
| `TAURI_DEBUG` | Enable debug mode |

## Build Output

```bash
# Development
dist/              # Vite build output

# Production
src-tauri/target/release/bundle/nsis/  # Windows installer
src-tauri/target/release/bundle/macos/  # macOS app
src-tauri/target/release/bundle/deb/   # Linux package
```
