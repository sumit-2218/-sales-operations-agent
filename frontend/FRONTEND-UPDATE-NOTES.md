# Sales Operations Agent — Futuristic Frontend Refresh

## Visual and navigation updates
- Replaced the light/white canvas with a midnight navy interface, teal/cyan accents, subtle grid textures, and dark workspace surfaces.
- Added a public product landing page at `/` with product explanation, illustrative pipeline UI, feature highlights, workflow steps, and clear Login / Register calls to action.
- Kept the dedicated Login (`/login`) and Register (`/register`) pages and restyled their surfaces to match the dark visual system.
- Moved the authenticated dashboard to `/dashboard`; the workspace navigation now links there. After login, users are directed to `/dashboard`.
- Existing protected pages remain available at `/leads`, `/import`, `/icp`, `/follow-ups`, `/profile`, and `/admin` routes.
- Kept admin access gated by the backend-reported role; frontend styling does not grant admin permissions.
- Preserved the Vercel SPA rewrite configuration.

## Local setup
1. Extract the archive.
2. From the `frontend` folder, run `npm install`.
3. Run `npm run dev`.
4. Open the local URL printed by Vite (usually `http://localhost:5173`).
5. The public landing page should appear before login. Use **Log in** or **Get started** to open the existing auth pages.
6. After login, the workspace dashboard is at `/dashboard`.
7. Run `npm run build` and `npm test` before deploying.

## Deployment reminders
- Deploy the contents of the `frontend` folder from the correct GitHub branch and Vercel project root.
- Confirm `VITE_API_BASE_URL` points to the intended API base. For the deployed backend, the usual value is `https://sales-operations-agent-1.onrender.com/api/v1`.
- Sign in using the actual administrator account and check its role in Profile. Admin navigation only appears for a backend-reported administrator role.
- Test `/dashboard`, `/leads`, `/profile`, `/admin`, `/admin/users`, and `/admin/system` after deployment.

The archive intentionally excludes `node_modules`; install dependencies on the target machine so platform-specific packages are selected correctly.
