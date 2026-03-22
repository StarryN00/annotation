import React, { useState, useEffect, useRef, useCallback } from 'react'
import { datasetApi, trainingApi } from '../services/api'

function Training() {
  const [datasets, setDatasets] = useState([])
  const [selectedDataset, setSelectedDataset] = useState('')
  const [modelSize, setModelSize] = useState('m')
  const [epochs, setEpochs] = useState(200)
  const [batchSize, setBatchSize] = useState(16)
  const [device, setDevice] = useState('0')
  const [tasks, setTasks] = useState([])
  const [activeTask, setActiveTask] = useState(null)
  const [progress, setProgress] = useState(null)
  const wsRef = useRef(null)

  const loadData = useCallback(async () => {
    try {
      const [datasetsRes, tasksRes] = await Promise.all([
        datasetApi.list(),
        trainingApi.list()
      ])
      setDatasets(datasetsRes.data)
      setTasks(tasksRes.data)
      if (datasetsRes.data.length > 0 && !selectedDataset) {
        setSelectedDataset(datasetsRes.data[0].id)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    }
  }, [selectedDataset])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    if (activeTask) {
      const wsUrl = `/ws/training/${activeTask.id}`
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

  const buildDataset = async () => {
    try {
      await datasetApi.build({
        train_ratio: 0.7,
        val_ratio: 0.2,
        test_ratio: 0.1,
        augment: true
      })
      loadData()
      alert('数据集构建成功')
    } catch (error) {
      alert('构建失败: ' + error.message)
    }
  }

  const startTraining = async () => {
    if (!selectedDataset) {
      alert('请先选择数据集')
      return
    }
    
    try {
      const response = await trainingApi.start({
        dataset_id: selectedDataset,
        model_size: modelSize,
        epochs,
        batch_size: batchSize,
        device
      })
      setActiveTask(response.data)
      loadData()
    } catch (error) {
      alert('启动训练失败: ' + error.message)
    }
  }

  const stopTraining = async (taskId) => {
    try {
      await trainingApi.stop(taskId)
      loadData()
    } catch (error) {
      alert('停止失败: ' + error.message)
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
    return <span className={`badge ${classes[status]}`}>{status}</span>
  }

  return (
    <div className="space-y-8">
      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-6">数据集</h2>
        
        <div className="flex items-center justify-between mb-6">
          <div className="text-stone-600">
            已有数据集: <span className="font-semibold text-emerald-900">{datasets.length}</span> 个
          </div>
          <button className="btn btn-secondary" onClick={buildDataset}>
            构建新数据集
          </button>
        </div>

        {datasets.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-stone-200">
                  <th className="text-left py-3 px-4 font-medium text-stone-600">名称</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">训练集</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">验证集</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">测试集</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map(dataset => (
                  <tr
                    key={dataset.id}
                    className={`border-b border-stone-100 hover:bg-stone-50 cursor-pointer ${
                      selectedDataset === dataset.id ? 'bg-emerald-50' : ''
                    }`}
                    onClick={() => setSelectedDataset(dataset.id)}
                  >
                    <td className="py-3 px-4">{dataset.name}</td>
                    <td className="py-3 px-4">{dataset.train_count}</td>
                    <td className="py-3 px-4">{dataset.val_count}</td>
                    <td className="py-3 px-4">{dataset.test_count}</td>
                    <td className="py-3 px-4 text-stone-500">
                      {new Date(dataset.created_at).toLocaleString('zh-CN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-6">开始训练</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">模型大小</label>
            <select
              value={modelSize}
              onChange={(e) => setModelSize(e.target.value)}
              className="input"
              disabled={!!activeTask}
            >
              <option value="n">YOLOv8n (最快)</option>
              <option value="s">YOLOv8s (快)</option>
              <option value="m">YOLOv8m (平衡)</option>
              <option value="l">YOLOv8l (精确)</option>
              <option value="x">YOLOv8x (最精确)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">训练轮数</label>
            <input
              type="number"
              value={epochs}
              onChange={(e) => setEpochs(parseInt(e.target.value))}
              className="input"
              min={1}
              max={1000}
              disabled={!!activeTask}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">批大小</label>
            <input
              type="number"
              value={batchSize}
              onChange={(e) => setBatchSize(parseInt(e.target.value))}
              className="input"
              min={1}
              max={128}
              disabled={!!activeTask}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-stone-700 mb-2">设备</label>
            <select
              value={device}
              onChange={(e) => setDevice(e.target.value)}
              className="input"
              disabled={!!activeTask}
            >
              <option value="0">GPU 0</option>
              <option value="cpu">CPU</option>
            </select>
          </div>
        </div>
        
        <button
          className={`btn btn-primary ${activeTask ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={startTraining}
          disabled={!!activeTask || !selectedDataset}
        >
          {activeTask ? '训练中...' : '开始训练'}
        </button>
        
        {progress && progress.type === 'training_progress' && (
          <div className="mt-6">
            <div className="flex items-center justify-between text-sm text-stone-600 mb-2">
              <span>Epoch {progress.epoch} / {progress.total_epochs}</span>
              <span>
                Loss: {progress.loss?.toFixed(4) || '-'} | 
                mAP50: {(progress.mAP50 * 100)?.toFixed(2) || '-'}% | 
                LR: {progress.lr?.toFixed(6) || '-'}
              </span>
            </div>
            <div className="w-full bg-stone-200 rounded-full h-2">
              <div
                className="bg-emerald-600 h-2 rounded-full transition-all"
                style={{ width: `${(progress.epoch / progress.total_epochs) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-4">训练任务历史</h2>
        
        {tasks.length === 0 ? (
          <p className="text-stone-500">暂无训练任务</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-stone-200">
                  <th className="text-left py-3 px-4 font-medium text-stone-600">模型</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">状态</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">进度</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">设备</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">创建时间</th>
                  <th className="text-left py-3 px-4 font-medium text-stone-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(task => (
                  <tr key={task.id} className="border-b border-stone-100 hover:bg-stone-50">
                    <td className="py-3 px-4">YOLOv8{task.model_size}</td>
                    <td className="py-3 px-4">{getStatusBadge(task.status)}</td>
                    <td className="py-3 px-4">
                      {task.current_epoch} / {task.total_epochs}
                      {task.status === 'running' && (
                        <span className="ml-2 text-stone-400">({Math.round(task.current_epoch / task.total_epochs * 100)}%)</span>
                      )}
                    </td>
                    <td className="py-3 px-4">{task.device}</td>
                    <td className="py-3 px-4 text-stone-500">
                      {new Date(task.created_at).toLocaleString('zh-CN')}
                    </td>
                    <td className="py-3 px-4">
                      {task.status === 'running' && (
                        <button
                          className="text-red-600 hover:text-red-800"
                          onClick={() => stopTraining(task.id)}
                        >
                          停止
                        </button>
                      )}
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

export default Training
