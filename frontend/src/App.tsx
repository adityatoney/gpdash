import { useEffect, lazy, Suspense } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { useFilterStore } from './stores/filterStore';
import { useActiveTab } from './hooks/useFilters';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Eager load overview (initial view), lazy load the rest
import { OverviewTab } from './components/tabs/OverviewTab';
const RegistrationTab = lazy(() => import('./components/tabs/RegistrationTab').then(m => ({ default: m.RegistrationTab })));
const RoomTab = lazy(() => import('./components/tabs/RoomTab').then(m => ({ default: m.RoomTab })));
const DiningTab = lazy(() => import('./components/tabs/DiningTab').then(m => ({ default: m.DiningTab })));
const AiInsightsTab = lazy(() => import('./components/tabs/AiInsightsTab').then(m => ({ default: m.AiInsightsTab })));
const RawDataTab = lazy(() => import('./components/tabs/RawDataTab').then(m => ({ default: m.RawDataTab })));

function TabContent() {
  const activeTab = useActiveTab();

  const content = (() => {
    switch (activeTab) {
      case 'overview': return <OverviewTab />;
      case 'registrations': return <RegistrationTab />;
      case 'rooms': return <RoomTab />;
      case 'dining': return <DiningTab />;
      case 'ai-insights': return <AiInsightsTab />;
      case 'raw-data': return <RawDataTab />;
      default: return <OverviewTab />;
    }
  })();

  return (
    <Suspense fallback={<LoadingSpinner message="Loading tab..." />}>
      {content}
    </Suspense>
  );
}

function App() {
  const initFromUrl = useFilterStore((s) => s.initFromUrl);

  useEffect(() => {
    initFromUrl();
  }, [initFromUrl]);

  return (
    <AppLayout>
      <TabContent />
    </AppLayout>
  );
}

export default App;
