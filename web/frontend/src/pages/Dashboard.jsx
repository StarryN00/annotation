import React, { useState, useEffect } from 'react'
import { imageApi, labelingApi, trainingApi, modelApi, healthApi } from '../services/api'

function Dashboard() {
  const [stats, setStats] = useState({
    totalImages: 0,
    labeledImages: 0,
    pendingTasks: 0,
    completedModels: 0,
    gpuAvailable: false
  })
  const [recentTasks, setRecentTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [imagesRes, labelingRes, trainingRes, modelsRes, healthRes] = await Promise.all([
        imageApi.list({ limit: 1 }),
        labelingApi.list(),
        trainingApi.list(),
        modelApi.list(),
        healthApi.check()
      ])

      const totalImages = imagesRes.data.total
      const images = await imageApi.list({ limit: totalImages > 100 ? 100 : totalImages })
      const labeledCount = images.data.items.filter(img => img.status === 'labeled' || img.status === 'verified').length

      setStats({
        totalImages,
        labeledImages: labeledCount,
        pendingTasks: labelingRes.data.filter(t => t.status === 'pending' || t.status === 'running').length +
                      trainingRes.data.filter(t => t.status === 'pending' || t.status === 'running').length,
        completedModels: modelsRes.data.length,
        gpuAvailable: healthRes.data.gpu_available
      })

      const allTasks = [
        ...labelingRes.data.slice(0, 5).map(t => ({ ...t, type: '标注' })),
        ...trainingRes.data.slice(0, 5).map(t => ({ ...t, type: '训练' }))
      ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5)
      
      setRecentTasks(allTasks)
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const classes = {
      pending: 'badge-pending',
      running: 'badge-running',
      completed: 'badge-completed',
      failed: 'badge-error',
      stopped: 'badge-error'
    }
    return <span className={`badge ${classes[status] || 'badge-pending'}`}>{status}</span>
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-stone-500">总图片数</p>
              <p className="text-3xl font-bold text-emerald-900">{stats.totalImages}</p>
            </div>
            <div className="p-3 bg-emerald-100 rounded-lg">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-stone-500 mt-2">已标注: {stats.labeledImages}</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-stone-500">进行中的任务</p>
              <p className="text-3xl font-bold text-amber-600">{stats.pendingTasks}</p>
            </div>
            <div className="p-3 bg-amber-100 rounded-lg">
              <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-stone-500 mt-2">标注 + 训练</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-stone-500">已训练模型</p>
              <p className="text-3xl font-bold text-blue-600">{stats.completedModels}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-stone-500 mt-2">可导出使用</p>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-stone-500">GPU状态</p>
              <p className={`text-3xl font-bold ${stats.gpuAvailable ? 'text-green-600' : 'text-stone-400'}`}>
                {stats.gpuAvailable ? '可用' : '不可用'}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${stats.gpuAvailable ? 'bg-green-100' : 'bg-stone-200'}`}>
              <svg className={`w-6 h-6 ${stats.gpuAvailable ? 'text-green-600' : 'text-stone-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-stone-500 mt-2">{stats.gpuAvailable ? '推荐使用GPU训练' : '将使用CPU训练'}</p>
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-4">最近任务</h2>
        {recentTasks.length === 0 ? (
          <p className="text-stone-500">暂无任务记录</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-stone-200">
                  <th className="text-left py-3 px-4 font-medium text-stone-600">类型</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">进度</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {recentTasks.map(task => (
                  <tr key={task.id} className="border-b border-stone-100 hover:bg-stone-50">
                    <td className="py-3 px-4">{task.type}</td>
                    <td className="py-3 px-4">{getStatusBadge(task.status)}</td>
                    <td className="py-3 px-4">
                      {task.processed_images !== undefined && (
                        `${task.processed_images} / ${task.total_images}`
                      )}
                      {task.current_epoch !== undefined && (
                        `${task.current_epoch} / ${task.total_epochs} epochs`
                      )}
                    </td>
                    <td className="py-3 px-4 text-stone-500">
                      {new Date(task.created_at).toLocaleString('zh-CN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
