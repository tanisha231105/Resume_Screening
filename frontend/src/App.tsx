import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/app/app-shell'
import { ResultsPage } from '@/pages/results'
import { UploadPage } from '@/pages/upload'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<UploadPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
