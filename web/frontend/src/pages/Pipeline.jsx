import React, { useState, useEffect, useCallback } from 'react'
import { pipelineApi } from '../services/api'

function Pipeline() {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState({
    provider: 'kimi',
    confidence: 'low',
    model_size: 'm',
    epochs: 200,
    batch_size: 8,
    device: 'mps',
    max_images: 200
  })

  const [trainingProgress, setTrainingProgress] = useState(null)

  const checkStatus = useCallback(async () => {
    try {
      const response = await pipelineApi.getStatus()
      setStatus(response.data)
      
      // 如果是训练阶段，获取详细的epoch进度
      if (response.data?.current_stage === 'training') {
        try {
          const progressRes = await pipelineApi.getTrainingProgress()
          setTrainingProgress(progressRes.data)
        } catch (e) {
          // 忽略错误
        }
      } else {
        setTrainingProgress(null)
      }
    } catch (error) {
      console.error('Failed to get status:', error)
    }
  }, [])

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [checkStatus])

  const startPipeline = async () => {
    setLoading(true)
    try {
      await pipelineApi.start(config)
      checkStatus()
    } catch (error) {
      alert('启动失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const stopPipeline = async () => {
    try {
      await pipelineApi.stop()
      checkStatus()
    } catch (error) {
      alert('停止失败: ' + error.message)
    }
  }

  const getStageText = (stage) => {
    const stageMap = {
      'labeling': '自动标注',
      'dataset': '构建数据集',
      'training': '模型训练',
      'finished': '完成',
      'idle': '空闲'
    }
    return stageMap[stage] || stage
  }

  const getStatusColor = (status) => {
    const colorMap = {
      'running': 'text-blue-600',
      'completed': 'text-green-600',
      'failed': 'text-red-600',
      'stopped': 'text-orange-600',
      'idle': 'text-stone-500'
    }
    return colorMap[status] || 'text-stone-600'
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-emerald-900">全自动流水线</h1>
        <div className="text-stone-500">
          无人值守：自动完成标注 → 数据集 → 训练
        </div>
      </div>

      {status?.status === 'running' ? (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
              <span className="text-lg font-semibold text-blue-900">
                流水线运行中
              </span>
            </div>
            <button 
              className="btn bg-red-600 text-white hover:bg-red-700"
              onClick={stopPipeline}
            >
              停止流水线
            </button>
          </div>
          
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-800">当前阶段: {getStageText(status.current_stage)}</span>
              <span className="text-blue-800 font-bold">{status.progress}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          </div>
          
          <div className="text-blue-700">
            {status.message}
          </div>
          
          {/* 训练阶段显示详细的epoch进度 */}
          {status.current_stage === 'training' && trainingProgress && trainingProgress.total_epochs > 0 && (
            <div className="mt-4 p-4 bg-white rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-blue-900 font-semibold">训练进度</span>
                <span className="text-blue-900 font-bold text-lg">
                  Epoch {trainingProgress.current_epoch} / {trainingProgress.total_epochs}
                </span>
              </div>
              <div className="w-full bg-blue-100 rounded-full h-4 mb-2">
                <div 
                  className="bg-emerald-500 h-4 rounded-full transition-all duration-500"
                  style={{ width: `${trainingProgress.progress_percent}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-sm text-blue-700">
                <span>已完成: {trainingProgress.progress_percent}%</span>
                <span>剩余: {trainingProgress.total_epochs - trainingProgress.current_epoch} 轮</span>
              </div>
            </div>
          )}
          
          {status.started_at && (
            <div className="text-sm text-blue-600 mt-2">
              开始时间: {new Date(status.started_at).toLocaleString('zh-CN')}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="card">
            <h2 className="text-xl font-bold text-emerald-900 mb-6">流水线配置</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">标注模型</label>
                <select
                  value={config.provider}
                  onChange={(e) => setConfig({...config, provider: e.target.value})}
                  className="input"
                >
                  <option value="kimi">Kimi</option>
                  <option value="claude">Claude</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Gemini</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">置信度阈值</label>
                <select
                  value={config.confidence}
                  onChange={(e) => setConfig({...config, confidence: e.target.value})}
                  className="input"
                >
                  <option value="high">高（仅高置信度）</option>
                  <option value="medium">中（中高置信度）</option>
                  <option value="low">低（保留所有）</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">YOLO模型大小</label>
                <select
                  value={config.model_size}
                  onChange={(e) => setConfig({...config, model_size: e.target.value})}
                  className="input"
                >
                  <option value="n">YOLOv8n（最快）</option>
                  <option value="s">YOLOv8s（快）</option>
                  <option value="m">YOLOv8m（平衡）</option>
                  <option value="l">YOLOv8l（精确）</option>
                  <option value="x">YOLOv8x（最精确）</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">训练轮数</label>
                <input
                  type="number"
                  value={config.epochs}
                  onChange={(e) => setConfig({...config, epochs: parseInt(e.target.value)})}
                  className="input"
                  min={10}
                  max={500}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">批大小</label>
                <input
                  type="number"
                  value={config.batch_size}
                  onChange={(e) => setConfig({...config, batch_size: parseInt(e.target.value)})}
                  className="input"
                  min={1}
                  max={64}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">训练设备</label>
                <select
                  value={config.device}
                  onChange={(e) => setConfig({...config, device: e.target.value})}
                  className="input"
                >
                  <option value="mps">Apple Silicon GPU (MPS)</option>
                  <option value="0">NVIDIA GPU 0</option>
                  <option value="cpu">CPU</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">
                  最大图片数
                  <span className="text-xs text-stone-500 ml-1">(0=使用全部)</span>
                </label>
                <input
                  type="number"
                  value={config.max_images}
                  onChange={(e) => setConfig({...config, max_images: parseInt(e.target.value) || 0})}
                  className="input"
                  min={0}
                  max={10000}
                  placeholder="0"
                />
                <p className="text-xs text-stone-500 mt-1">
                  随机选择指定数量的图片用于训练，0表示使用所有图片
                </p>
              </div>
            </div>
            
            <div className="mt-6 flex items-center gap-4">
              <button
                className={`btn btn-primary ${loading ? 'opacity-50' : ''}`}
                onClick={startPipeline}
                disabled={loading}
              >
                {loading ? '启动中...' : '开始全自动流水线'}
              </button>
              
              <p className="text-stone-500 text-sm">
                启动后将自动完成：标注所有图片 → 构建数据集 → 训练模型
              </p>
            </div>
          </div>

          {status && status.status !== 'idle' && (
            <div className={`card ${
              status.status === 'completed' ? 'bg-green-50 border-green-200' :
              status.status === 'failed' ? 'bg-red-50 border-red-200' :
              'bg-orange-50 border-orange-200'
            }`}>
              <h3 className={`font-semibold ${getStatusColor(status.status)}`}>
                {status.status === 'completed' ? '✅ 流水线完成' :
                 status.status === 'failed' ? '❌ 流水线失败' :
                 status.status === 'stopped' ? '⏹️ 流水线已停止' :
                 '流水线状态'}
              </h3>
              <p className="mt-2 text-stone-700">{status.message}</p>
              
              {status.results && (
                <div className="mt-4 text-sm text-stone-600">
                  {status.results.labeled_count && (
                    <div>标注图片数: {status.results.labeled_count}</div>
                  )}
                  {status.results.dataset_id && (
                    <div>数据集ID: {status.results.dataset_id}</div>
                  )}
                  {status.results.training_task_id && (
                    <div>训练任务ID: {status.results.training_task_id}</div>
                  )}
                </div>
              )}
              
              {status.completed_at && (
                <div className="text-sm text-stone-500 mt-2">
                  完成时间: {new Date(status.completed_at).toLocaleString('zh-CN')}
                </div>
              )}
            </div>
          )}
        </>
      )}

      <div className="card">
        <h2 className="text-xl font-bold text-emerald-900 mb-4">流水线说明</h2>
        
        <div className="space-y-4 text-stone-600">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">1</div>
            <div>
              <div className="font-medium text-stone-800">自动标注</div>
              <div className="text-sm">使用AI模型自动检测所有上传图片中的虫巢，支持批量处理</div>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">2</div>
            <div>
              <div className="font-medium text-stone-800">构建数据集</div>
              <div className="text-sm">自动划分训练集(70%)、验证集(20%)、测试集(10%)</div>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">3</div>
            <div>
              <div className="font-medium text-stone-800">模型训练</div>
              <div className="text-sm">使用YOLOv8训练目标检测模型，自动保存最佳模型</div>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">4</div>
            <div>
              <div className="font-medium text-stone-800">导出结果</div>
              <div className="text-sm">训练完成后可在模型管理页面下载训练好的模型</div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-yellow-50 rounded-lg text-sm text-yellow-800">
          <strong>注意事项：</strong>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>请确保已上传图片并设置API密钥</li>
            <li>建议至少上传10张图片以获得较好的训练效果</li>
            <li>训练过程可能需要较长时间，请保持页面打开或后台运行</li>
            <li>可以随时停止流水线，已完成的任务会保留</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default Pipeline
