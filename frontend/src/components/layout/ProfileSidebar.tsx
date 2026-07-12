'use client';

import { UserProfile } from '@/lib/types';
import { User, Briefcase, DollarSign, ShieldCheck, CheckCircle2, XCircle, Clock } from 'lucide-react';

const statusIcon = (status: string) => {
  if (status === 'done') return <CheckCircle2 size={14} className="text-green-600" />;
  if (status === 'pending') return <Clock size={14} className="text-amber-500" />;
  return <XCircle size={14} className="text-gray-300" />;
};

export function ProfileSidebar({ profile }: { profile: UserProfile }) {
  return (
    <aside className="w-64 shrink-0 h-full bg-gray-50 border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-5 border-b border-gray-200">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
            <User size={16} className="text-gray-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">{profile.business_name || 'Belum ada nama'}</p>
            <p className="text-xs text-gray-400">Profil Bisnis</p>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="p-5 space-y-4 flex-1 overflow-y-auto">
        <div>
          <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wider mb-2">Informasi</p>
          <div className="space-y-3">
            <div className="flex items-start gap-2.5">
              <Briefcase size={14} className="text-gray-400 mt-0.5" />
              <div>
                <p className="text-[11px] text-gray-400">Tipe Usaha</p>
                <p className="text-sm text-gray-700">{profile.business_type || '—'}</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <DollarSign size={14} className="text-gray-400 mt-0.5" />
              <div>
                <p className="text-[11px] text-gray-400">Kategori Produk</p>
                <p className="text-sm text-gray-700">{profile.product_category || '—'}</p>
              </div>
            </div>
            {profile.capital_hpp && (
              <div className="flex items-start gap-2.5">
                <DollarSign size={14} className="text-gray-400 mt-0.5" />
                <div>
                  <p className="text-[11px] text-gray-400">Modal / HPP</p>
                  <p className="text-sm text-gray-700">Rp{profile.capital_hpp.toLocaleString()}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Compliance */}
        <div>
          <div className="flex items-center gap-1.5 mb-2">
            <ShieldCheck size={12} className="text-gray-400" />
            <p className="text-[11px] font-medium text-gray-400 uppercase tracking-wider">Status Legalitas</p>
          </div>
          <div className="space-y-1.5">
            {profile.compliance_status.map((c) => (
              <div key={c.item} className="flex items-center justify-between py-1.5 px-2 rounded bg-white border border-gray-100">
                <span className="text-sm text-gray-700">{c.item}</span>
                {statusIcon(c.status)}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <p className="text-[10px] text-gray-300 text-center">Mock Profile · V1 Demo</p>
      </div>
    </aside>
  );
}
