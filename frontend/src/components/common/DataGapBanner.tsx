export function DataGapBanner({ gaps, year }: { gaps: string[]; year?: number }) {
  if (gaps.length === 0) return null;
  const yearText = year ? ` for ${year}` : '';
  return (
    <div className="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
      <svg className="h-4 w-4 shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
      </svg>
      <span>
        <strong className="font-medium">{gaps.map(g => g.charAt(0).toUpperCase() + g.slice(1)).join(', ')} data</strong>
        {` not available${yearText}`}
      </span>
    </div>
  );
}
