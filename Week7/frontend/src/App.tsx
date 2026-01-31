import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import type { ProjectState } from './types';
import './index.css';

function App() {
  const [projectState, setProjectState] = useState<ProjectState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProject();
  }, []);

  const loadProject = async () => {
    try {
      setLoading(true);
      const state = await api.getProject();
      setProjectState(state);
    } catch (err) {
      setError('加载项目失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-xl">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            AI Slide Generator
          </h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">项目状态</h2>
          <pre className="bg-gray-50 p-4 rounded overflow-auto">
            {JSON.stringify(projectState, null, 2)}
          </pre>
        </div>
      </main>
    </div>
  );
}

export default App;
