import { useParams } from "react-router-dom";
import { useApi, StateBanner } from "../lib/useApi";

export default function Referrals() {
  const { workspaceId } = useParams();
  const { data: referrals, loading, error } = useApi(`/workspaces/${workspaceId}/referrals`);

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">Referrals</h1>
      <p className="text-sm text-slate-500">Referral links, position tracking, and rewards. Signups attribute a growth event back to the referral code.</p>

      <StateBanner loading={loading} error={error} empty={referrals && referrals.length === 0} />

      {referrals && referrals.length > 0 && (
        <table className="w-full text-sm bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200 dark:border-slate-800">
              <th className="p-2">#</th><th>Code</th><th>Referred email</th><th>Reward</th>
            </tr>
          </thead>
          <tbody>
            {referrals.map((r) => (
              <tr key={r.id} className="border-t border-slate-100 dark:border-slate-800">
                <td className="p-2">{r.position}</td>
                <td><code>{r.code}</code></td>
                <td>{r.referred_email || "-"}</td>
                <td>{r.reward || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
