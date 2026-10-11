import React from 'react';
import { createBrowserRouter, Link } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { DiscoveryPage } from '../features/catalog/DiscoveryPage';
import { MediaDetailPage } from '../features/catalog/MediaDetailPage';
import { DiaryPage } from '../features/diary/DiaryPage';
import { CollectionsPage } from '../features/collections/CollectionsPage';
import { ProfilePage } from '../features/profile/ProfilePage';
import { LoginPage } from '../features/auth/LoginPage';
import { FoundationDemoPage } from '../features/catalog/FoundationDemoPage';
import { EmptyState } from '../components/feedback/EmptyState';
import { Button } from '../components/ui/Button';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DiscoveryPage />,
      },
      {
        path: 'discovery',
        element: <DiscoveryPage />,
      },
      {
        path: 'media/:slug',
        element: <MediaDetailPage />,
      },
      {
        path: 'diary',
        element: <DiaryPage />,
      },
      {
        path: 'collections',
        element: <CollectionsPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'demo',
        element: <FoundationDemoPage />,
      },
      {
        path: 'recommendations',
        element: <DiscoveryPage />,
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
