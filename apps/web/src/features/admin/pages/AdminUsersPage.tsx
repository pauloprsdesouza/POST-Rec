import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/features/auth/context/AuthContext";
import { adminService } from "@/shared/api";
import type { AdminUserRecord, UserRole } from "@/shared/types/api";
import { PageHeader } from "@/shared/ui/PageHeader";
import { PageShell } from "@/shared/ui/PageShell";
import { Panel } from "@/shared/ui/Panel";
import { InlineAlert } from "@/shared/ui/InlineAlert";
import { LoadingSpinner } from "@/shared/ui/LoadingSpinner";

export function AdminUsersPage() {
  const { t } = useTranslation();
  const { accessToken, user: currentUser } = useAuth();
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await adminService.listUsers(accessToken, { limit: 100 });
      setUsers(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("admin.loadError"));
    } finally {
      setLoading(false);
    }
  }, [accessToken, t]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  async function handleRoleChange(userId: string, role: UserRole) {
    if (!accessToken) {
      return;
    }
    setUpdatingId(userId);
    setError(null);
    try {
      const updated = await adminService.updateUserRole(accessToken, userId, role);
      setUsers((current) => current.map((item) => (item.id === userId ? updated : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("admin.users.updateError"));
    } finally {
      setUpdatingId(null);
    }
  }

  if (loading) {
    return (
      <PageShell pageClass="admin-page">
        <div className="page-stack page-stack--tight">
          <LoadingSpinner label={t("admin.loading")} />
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell pageClass="admin-page">
      <div className="page-stack page-stack--tight">
        <PageHeader
          title={t("admin.users.title")}
          subtitle={t("admin.users.subtitle", { count: total })}
        />

        {error ? <InlineAlert variant="danger">{error}</InlineAlert> : null}

        <Panel as="section" className="admin-section">
          <div className="table-responsive">
            <table className="table table-sm admin-table">
              <thead>
                <tr>
                  <th>{t("admin.users.name")}</th>
                  <th>{t("admin.users.email")}</th>
                  <th>{t("admin.users.role")}</th>
                  <th>{t("admin.users.status")}</th>
                </tr>
              </thead>
              <tbody>
                {users.map((row) => {
                  const isSelf = row.id === currentUser?.userId;
                  return (
                    <tr key={row.id}>
                      <td data-label={t("admin.users.name")}>
                        <span className="admin-table__primary">{row.full_name ?? t("common.unknown")}</span>
                        {isSelf ? (
                          <span className="admin-table__secondary">{t("admin.users.you")}</span>
                        ) : null}
                      </td>
                      <td data-label={t("admin.users.email")}>{row.email ?? "—"}</td>
                      <td data-label={t("admin.users.role")}>
                        <select
                          className="form-select form-select-sm admin-role-select"
                          value={row.role}
                          disabled={updatingId === row.id || (isSelf && row.role === "admin")}
                          aria-label={t("admin.users.roleFor", { name: row.full_name ?? row.email ?? row.id })}
                          onChange={(event) => {
                            void handleRoleChange(row.id, event.target.value as UserRole);
                          }}
                        >
                          <option value="researcher">{t("admin.users.researcher")}</option>
                          <option value="admin">{t("admin.users.admin")}</option>
                        </select>
                      </td>
                      <td data-label={t("admin.users.status")}>
                        {row.is_active ? (
                          <span className="admin-status-pill admin-status-pill--ok">{t("admin.users.active")}</span>
                        ) : (
                          <span className="admin-status-pill admin-status-pill--warn">
                            {t("admin.users.inactive")}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </PageShell>
  );
}
