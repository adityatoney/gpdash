import { ReactNode } from 'react';

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  isLoading?: boolean;
  isEmpty?: boolean;
  height?: number;
}

export function ChartContainer({ title, subtitle, children, className = '', isLoading, isEmpty, height = 300 }: ChartContainerProps) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}>
      <div className="px-6 pt-5 pb-2">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className="px-4 pb-4" style={{ height }}>
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="w-full h-3/4 bg-gray-100 rounded-lg animate-pulse" />
          </div>
        ) : isEmpty ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <svg className="h-10 w-10 mb-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            <span className="text-sm">No data available</span>
          </div>
        ) : children}
      </div>
    </div>
  );
}
