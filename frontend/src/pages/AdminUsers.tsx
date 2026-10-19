import { Badge, Card, ErrorBox, Spinner, useToast } from "../components/ui";
import { normalizeRole, useAuth } from "../hooks/useAuth";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { apiErrorMessage } from "../utils/errors";
import { fmtDate } from "../utils/format";

export default function AdminUsers() {
  const { user: me } = useAuth();
  const toast = useToast();
  const { data, loading, error, reload } = useAsync(api.adminUsers, []);
  async function patch(id: number, b: { role?: string; is_active?: boolean }) {
    try { await api.adminUpdateUser(id, b); toast("success", "User updated"); await reload(); } catch (e) { toast("error", apiErrorMessage(e)); }
  }
  return (
    <>
      <h1 className="text-2xl font-bold">User management</h1>
      {loading ? <Spinner /> : error || !data ? <ErrorBox problem={error} onRetry={reload} /> : (
        <Card><table className="w-full text-left text-sm"><thead className="border-b text-slate-500"><tr><th className="p-2">Name</th><th className="p-2">Email</th><th className="p-2">Role</th><th className="p-2">Status</th><th className="p-2">Created</th><th className="p-2">Action</th></tr></thead>
          <tbody>{data.items.map((u) => (
            <tr key={u.id} className="border-b last:border-0"><td className="p-2">{u.name}</td><td className="p-2">{u.email}</td>
              <td className="p-2"><select aria-label={`Role for ${u.email}`} disabled={u.id === me?.id} className="rounded-md border px-2 py-1" value={normalizeRole(u.role)} onChange={(e) => patch(u.id, { role: e.target.value })}>
                <option value="sales_rep">Sales rep</option><option value="manager">Manager</option><option value="admin">Administrator</option></select></td>
              <td className="p-2"><Badge value={u.is_active ? "active" : "disabled"} danger={!u.is_active} /></td><td className="p-2">{fmtDate(u.created_at)}</td>
              <td className="p-2"><button className="rounded-md border px-2 py-1 hover:bg-slate-100 disabled:opacity-40" disabled={u.id === me?.id} onClick={() => patch(u.id, { is_active: !u.is_active })}>{u.is_active ? "Disable" : "Enable"}</button></td></tr>))}</tbody></table></Card>)}
    </>
  );
}
