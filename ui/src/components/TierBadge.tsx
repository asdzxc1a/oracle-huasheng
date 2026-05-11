interface TierBadgeProps {
  tier: string;
}

const TIER_STYLES: Record<string, string> = {
  A: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  B: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  C: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  F: "bg-rose-500/20 text-rose-400 border-rose-500/30",
};

export function TierBadge({ tier }: TierBadgeProps) {
  const style = TIER_STYLES[tier.toUpperCase()] || TIER_STYLES.C;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${style}`}
      title={`Tier ${tier.toUpperCase()} claim`}
    >
      T{tier.toUpperCase()}
    </span>
  );
}
