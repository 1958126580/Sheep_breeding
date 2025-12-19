import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Dashboard from '../pages/dashboard';
import FarmList from '../pages/farm/FarmList';
import AnimalList from '../pages/animal/AnimalList';
import BreedingAnalysis from '../pages/breeding/BreedingAnalysis';

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'farm', element: <FarmList /> },
      { path: 'animal', element: <AnimalList /> },
      { path: 'breeding', element: <BreedingAnalysis /> },
    ],
  },
]);

export default router;
