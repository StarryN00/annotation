import React, { useState, useEffect, useCallback } from 'react'
import { modelApi } from '../services/api'

function Models() {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)

  const loadModels = useCallback(async () => {
    try {
      const response = await modelApi.list()
      setModels(response.data)
    } catch (error) {
      console.error('Failed to load models:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadModels()
  }, [loadModels])

  const handleExport = async (id, format) => {
    try {
      const response = await modelApi.export(id, format)
      window.open(response.data.download_url, '_blank')
    } catch (error) {
      alert('导出失败: ' + error.message)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定要删除这个模型吗？')) return
    try {
      await modelApi.delete(id)
      loadModels()
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }

  const handleDownload = (id, format) => {
    window.open(modelApi.download(id, format), '_blank')
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-emerald-900">模型管理</h1>
        <span className="text-stone-600">共 {models.length} 个模型</span>
      </div>

      {models.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-stone-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
          <p className="text-stone-500">暂无训练好的模型</p>
          <p className="text-stone-400 text-sm mt-2">请先完成训练任务</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {models.map(model => (
            <div key={model.id} className="card">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-emerald-900">{model.name}</h3>
                  <p className="text-sm text-stone-500">
                    创建于 {new Date(model.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <span className="badge bg-stone-100 text-stone-600">{model.format.toUpperCase()}</span>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-stone-50 rounded-lg">
                  <p className="text-xs text-stone-500">mAP50</p>
                  <p className="text-lg font-semibold text-emerald-700">
                    {(model.metrics?.mAP50 * 100)?.toFixed(1) || '-'}%
                  </p>
                </div>
                <div className="text-center p-3 bg-stone-50 rounded-lg">
                  <p className="text-xs text-stone-500">精确率</p>
                  <p className="text-lg font-semibold text-emerald-700">
                    {(model.metrics?.precision * 100)?.toFixed(1) || '-'}%
                  </p>
                </div>
                <div className="text-center p-3 bg-stone-50 rounded-lg">
                  <p className="text-xs text-stone-500">召回率</p>
                  <p className="text-lg font-semibold text-emerald-700">
                    {(model.metrics?.recall * 100)?.toFixed(1) || '-'}%
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm text-stone-500 mb-4">
                <span>文件大小: {model.size_mb.toFixed(2)} MB</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  className="btn btn-outline text-sm flex-1"
                  onClick={() => handleDownload(model.id, 'pt')}
                >
                  下载 PyTorch
                </button>
                <button
                  className="btn btn-outline text-sm flex-1"
                  onClick={() => handleExport(model.id, 'onnx')}
                >
                  导出 ONNX
                </button>
                <button
                  className="p-2 text-red-500 hover:text-red-700"
                  onClick={() => handleDelete(model.id)}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Models
