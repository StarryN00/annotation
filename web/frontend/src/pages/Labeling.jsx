import React, { useState, useEffect, useRef, useCallback } from 'react'
import { imageApi, labelingApi } from '../services/api'

function Labeling() {
  const [images, setImages] = useState([])
  const [selectedProvider, setSelectedProvider] = useState('kimi')
  const [selectedConfidence, setSelectedConfidence] = useState('medium')
  const [tasks, setTasks] = useState([])
  const [activeTask, setActiveTask] = useState(null)
  const [progress, setProgress] = useState(null)
  const wsRef = useRef(null)

  const [imageFilter, setImageFilter] = useState('pending')

  const loadData = useCallback(async () => {
    try {
      const params = imageFilter === 'all' ? { limit: 100 } : { status: imageFilter, limit: 100 }
      const [imagesRes, tasksRes] = await Promise.all([
        imageApi.list(params),
        labelingApi.list()
      ])
      setImages(imagesRes.data.items)
      setTasks(tasksRes.data)
    } catch (error) {
      console.error('Failed to load data:', error)
    }
  }, [imageFilter])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (activeTask) {
      const wsUrl = `/api/labeling/ws/${activeTask.id}`
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setProgress(data)
        
        if (data.type === 'completed' || data.type === 'error') {
          setTimeout(() => {
            setActiveTask(null)
            setProgress(null)
            loadData()
          }, 3000)
        }
      }
      
      return () => {
        wsRef.current?.close()
      }
    }
  }, [activeTask, loadData])

  const startLabeling = async () => {
    if (images.length === 0) {
      alert('没有待标注的图片')
      return
    }
    
    try {
      const imageIds = images.map(img => img.id)
      const response = await labelingApi.start({
        image_ids: imageIds,
        provider: selectedProvider,
        confidence: selectedConfidence
      })
      setActiveTask(response.data)
      loadData()
    } catch (error) {
      alert('启动标注失败: ' + error.message)
    }
  }

  const getStatusBadge = (status) => {
    const classes = {
      pending: 'badge-pending',
      running: 'badge-running',
      completed: 'badge-completed',
      failed: 'badge-error'
    }
    return <span className={`badge ${classes[status]}`}>{status}</span>
  }

  return (
    <div className="space-y-8">
      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-6">开始自动标注</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">图片状态筛选</label>
            <select
              value={imageFilter}
              onChange={(e) => setImageFilter(e.target.value)}
              className="input"
            >
              <option value="pending">待标注</option>
              <option value="labeled">已标注</option>
              <option value="verified">已验证</option>
              <option value="all">全部</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">选择模型</label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="input"
              disabled={!!activeTask}
            >
              <option value="kimi">Kimi (moonshot-v1-8k-vision)</option>
              <option value="claude">Claude (Sonnet 4)</option>
              <option value="openai">OpenAI (GPT-4o)</option>
              <option value="gemini">Gemini (2.5 Pro)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">置信度阈值</label>
            <select
              value={selectedConfidence}
              onChange={(e) => setSelectedConfidence(e.target.value)}
              className="input"
              disabled={!!activeTask}
            >
              <option value="high">高 (仅保留高置信度结果)</option>
              <option value="medium">中 (平衡质量与数量)</option>
              <option value="low">低 (保留所有结果)</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="text-stone-600">
            待标注图片: <span className="font-semibold text-emerald-900">{images.length}</span> 张
          </div>
          
          <button
            className={`btn btn-primary ${activeTask ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={startLabeling}
            disabled={!!activeTask || images.length === 0}
          >
            {activeTask ? '标注进行中...' : '开始标注'}
          </button>
        </div>
        
        {progress && progress.type === 'progress' && (
          <div className="mt-6">
            <div className="flex items-center justify-between text-sm text-stone-600 mb-2">
              <span>处理中: {progress.image_name}</span>
              <span>{progress.current} / {progress.total} ({Math.round(progress.current / progress.total * 100)}%)</span>
            </div>
            <div className="w-full bg-stone-200 rounded-full h-2">
              <div
                className="bg-emerald-600 h-2 rounded-full transition-all"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              />
            </div>
            <p className="text-sm text-stone-500 mt-2">检测到 {progress.detections_count} 个虫巢</p>
          </div>
        )}
        
        {progress && progress.type === 'completed' && (
          <div className="mt-6 p-4 bg-green-50 text-green-800 rounded-lg">
            标注完成！成功: {progress.success}, 失败: {progress.error}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-4">标注任务历史</h2>
        
        {tasks.length === 0 ? (
          <p className="text-stone-500">暂无标注任务</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-stone-200">
                  <th className="text-left py-3 px-4 font-medium text-stone-600">模型</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">进度</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">置信度</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(task => (
                  <tr key={task.id} className="border-b border-stone-100 hover:bg-stone-50">
                    <td className="py-3 px-4 capitalize">{task.provider}</td>
                    <td className="py-3 px-4">{getStatusBadge(task.status)}</td>
                    <td className="py-3 px-4">
                      {task.processed_images} / {task.total_images}
                      {task.status === 'running' && (
                        <span className="ml-2 text-stone-400">({Math.round(task.processed_images / task.total_images * 100)}%)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 capitalize">{task.confidence}</td>
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

export default Labeling
