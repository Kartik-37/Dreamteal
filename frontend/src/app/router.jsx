import React from 'react';
import { createBrowserRouter, Link } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { FoundationDemoPage } from '../features/catalog/FoundationDemoPage';
import { EmptyState } from '../components/feedback/EmptyState';
import { Button } from '../components/ui/Button';

function PhasePlaceholder({ title, description }) {
  return (
    <div className="max-w-4xl mx-auto px-4 py-20 w-full">
      <EmptyState
        title={title}
        description={description}
        action={
          <Link to="/">
            <Button variant="secondary" size="sm">
              Return to Explore Foundation
            </Button>
          </Link>
        }
      />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <FoundationDemoPage />,
      },
      {
        path: 'diary',
        element: (
          <PhasePlaceholder
            title="Diary & History Timeline"
            description="Chronological media logging with session snapshots and rewatch tracking is scheduled for Phase 5 implementation."
          />
        ),
      },
      {
        path: 'collections',
        element: (
          <PhasePlaceholder
            title="Curated Collections"
            description="Custom media lists, favorites, and cross-category collections are scheduled for Phase 5 implementation."
          />
        ),
      },
      {
        path: 'recommendations',
        element: (
          <PhasePlaceholder
            title="Recommendation Hub"
            description="Deterministic explainable discovery powered by DreamTeal's recommendation engine is scheduled for Phase 5 implementation."
          />
        ),
      },
      {
        path: '*',
        element: (
          <div className="max-w-4xl mx-auto px-4 py-20 w-full">
            <EmptyState
              title="404 — Page Not Found"
              description="The requested page does not exist."
              action={
                <Link to="/">
                  <Button variant="primary" size="sm">
                    Return to Home
                  </Button>
                </Link>
              }
            />
          </div>
        ),
      },
    ],
  },
]);
