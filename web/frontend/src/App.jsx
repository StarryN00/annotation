import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Images from './pages/Images'
import Labeling from './pages/Labeling'
import Training from './pages/Training'
import Models from './pages/Models'
import Pipeline from './pages/Pipeline'

function App() {
  return (
    <div className="min-h-screen bg-stone-50">
      <nav className="bg-emerald-900 text-white shadow-lg">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <svg className="w-8 h-8 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
              <span className="text-xl font-bold">NestLabel</span>
            </div>
            
            <div className="flex space-x-1">
              <NavLink to="/" className={({isActive}) =>
                `px-4 py-2 rounded-lg transition-colors ${isActive ? 'bg-emerald-800 text-white' : 'text-emerald-100 hover:bg-emerald-800'}`
              }>
                概览
              </NavLink>
              <NavLink to="/images" className={({isActive}) =>
                `px-4 py-2 rounded-lg transition-colors ${isActive ? 'bg-emerald-800 text-white' : 'text-emerald-100 hover:bg-emerald-800'}`
              }>
                图片
              </NavLink>
              <NavLink to="/labeling" className={({isActive}) =>
                `px-4 py-2 rounded-lg transition-colors ${isActive ? 'bg-emerald-800 text-white' : 'text-emerald-100 hover:bg-emerald-800'}`
              }>
                标注
              </NavLink>
              <NavLink to="/training" className={({isActive}) =>
                `px-4 py-2 rounded-lg transition-colors ${isActive ? 'bg-emerald-800 text-white' : 'text-emerald-100 hover:bg-emerald-800'}`
              }>
                训练
              </NavLink>
              <NavLink to="/models" className={({isActive}) =>
                `px-4 py-2 rounded-lg transition-colors ${isActive ? 'bg-emerald-800 text-white' : 'text-emerald-100 hover:bg-emerald-800'}`
              }>
                模型
              </NavLink>
              <NavLink to="/pipeline" className={({isActive}) =>
                `px-4 py-2 rounded-lg transition-colors ${isActive ? 'bg-amber-600 text-white' : 'text-amber-200 hover:bg-amber-600'}`
              }>
                全自动
              </NavLink>
            </div>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/images" element={<Images />} />
          <Route path="/labeling" element={<Labeling />} />
          <Route path="/training" element={<Training />} />
          <Route path="/models" element={<Models />} />
          <Route path="/pipeline" element={<Pipeline />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
