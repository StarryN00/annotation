import React, { useState, useEffect, useCallback, useRef } from 'react'
import { imageApi } from '../services/api'
import DetectionCanvas from '../components/DetectionCanvas'

function Images() {
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [selectedImages, setSelectedImages] = useState(new Set())
  const [uploading, setUploading] = useState(false)
  const [selectedImage, setSelectedImage] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [directoryPath, setDirectoryPath] = useState('')
  const [searchKeyword, setSearchKeyword] = useState('')
  const searchKeywordRef = useRef(searchKeyword)
  const limit = 20

  useEffect(() => {
    searchKeywordRef.current = searchKeyword
  }, [searchKeyword])

  const loadImages = useCallback(async () => {
    try {
      const params = { page, limit }
      if (searchKeywordRef.current.trim()) {
        params.search = searchKeywordRef.current.trim()
      }
      const response = await imageApi.list(params)
      setImages(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to load images:', error)
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    loadImages()
  }, [loadImages])

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return

    const maxFileSize = 20 * 1024 * 1024
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    const allowedExts = /\.(jpg|jpeg|png|webp)$/i

    const validFiles = []
    const skippedFiles = []

    files.forEach(file => {
      const isValidType = allowedTypes.includes(file.type) || allowedExts.test(file.name)
      const isValidSize = file.size <= maxFileSize

      if (isValidType && isValidSize) {
        validFiles.push(file)
      } else {
        const reason = !isValidType ? '格式不支持' : '超过20MB'
        skippedFiles.push(`${file.name} (${reason})`)
      }
    })

    if (validFiles.length === 0) {
      alert(`没有符合要求的文件可上传。\n\n跳过了 ${skippedFiles.length} 个文件:\n${skippedFiles.slice(0, 5).join('\n')}${skippedFiles.length > 5 ? '\n...' : ''}`)
      e.target.value = ''
      return
    }

    if (skippedFiles.length > 0) {
      const skipMsg = skippedFiles.length <= 3
        ? skippedFiles.join('\n')
        : skippedFiles.slice(0, 3).join('\n') + `\n...等共${skippedFiles.length}个文件`
      alert(`将上传 ${validFiles.length} 个文件，跳过 ${skippedFiles.length} 个不符合要求的文件:\n${skipMsg}`)
    }

    const batchSize = 10
    const totalBatches = Math.ceil(validFiles.length / batchSize)

    if (validFiles.length > batchSize) {
      if (!confirm(`将上传 ${validFiles.length} 张图片，分 ${totalBatches} 批上传，是否继续？`)) {
        e.target.value = ''
        return
      }
    }

    setUploading(true)
    let successCount = 0
    let errorCount = 0
    const errors = []

    try {
      for (let i = 0; i < validFiles.length; i += batchSize) {
        const batch = validFiles.slice(i, i + batchSize)
        const batchNum = Math.floor(i / batchSize) + 1
        
        try {
          const response = await imageApi.upload(batch)
          successCount += response.data.count
        } catch (error) {
          errorCount += batch.length
          errors.push(`第${batchNum}批: ${error.response?.data?.detail || error.message}`)
        }
        
        // 更新上传进度
        if (totalBatches > 1) {
          console.log(`上传进度: ${batchNum}/${totalBatches}`)
        }
      }

      // 显示上传结果
      let message = `上传完成！成功 ${successCount} 张`
      if (errorCount > 0) {
        message += `，失败 ${errorCount} 张`
        console.error('上传错误详情:', errors)
      }
      alert(message)
      
      loadImages()
    } catch (error) {
      alert('上传失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
      // 清空文件选择，允许重复选择同一文件
      e.target.value = ''
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定要删除这张图片吗？')) return
    try {
      await imageApi.delete(id)
      loadImages()
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }

  const toggleSelect = (id, e) => {
    e?.stopPropagation()
    const newSet = new Set(selectedImages)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setSelectedImages(newSet)
  }

  const selectAll = () => {
    const allIds = images.map(img => img.id)
    setSelectedImages(new Set(allIds))
  }

  const deselectAll = () => {
    setSelectedImages(new Set())
  }

  const handleBatchDelete = async () => {
    if (selectedImages.size === 0) return
    if (!confirm(`确定要删除选中的 ${selectedImages.size} 张图片吗？`)) return
    
    try {
      const promises = Array.from(selectedImages).map(id => imageApi.delete(id))
      await Promise.all(promises)
      setSelectedImages(new Set())
      loadImages()
    } catch (error) {
      alert('批量删除失败: ' + error.message)
    }
  }

  const handleScanDirectory = async () => {
    if (!directoryPath.trim()) {
      alert('请输入目录路径')
      return
    }
    
    setScanning(true)
    try {
      const response = await imageApi.scanDirectory(directoryPath.trim())
      alert(`导入成功！${response.data.message || `导入了 ${response.data.count} 张图片`}`)
      setDirectoryPath('')
      loadImages()
    } catch (error) {
      alert('扫描目录失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setScanning(false)
    }
  }

  const getStatusBadge = (status) => {
    const classes = {
      pending: 'badge-pending',
      labeling: 'badge-running',
      labeled: 'badge-completed',
      verified: 'bg-emerald-100 text-emerald-800',
      error: 'badge-error'
    }
    const labels = {
      pending: '待标注',
      labeling: '标注中',
      labeled: '已标注',
      verified: '已验证',
      error: '错误'
    }
    return <span className={`badge ${classes[status] || 'badge-pending'}`}>{labels[status] || status}</span>
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-emerald-900">图片管理</h1>
        <div className="flex items-center gap-3">
          <div className="relative">
            <input
              type="text"
              placeholder="搜索图片文件名..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onKeyPress={(e) => {
              if (e.key === 'Enter') {
                if (page === 1) {
                  loadImages()
                } else {
                  setPage(1)
                }
              }
            }}
              className="input pl-10 w-64"
            />
            <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {searchKeyword && (
              <button
                onClick={() => {
                  setSearchKeyword('')
                  searchKeywordRef.current = ''
                  setPage(1)
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <button
            className="btn btn-outline"
            onClick={() => {
              if (page === 1) {
                loadImages()
              } else {
                setPage(1)
              }
            }}
          >
            搜索
          </button>
          {selectedImages.size > 0 && (
            <>
              <span className="text-emerald-700 font-medium">已选择 {selectedImages.size} 张</span>
              <button className="btn btn-outline" onClick={handleBatchDelete}>
                批量删除
              </button>
              <button className="btn btn-outline" onClick={deselectAll}>
                取消全选
              </button>
            </>
          )}
          {images.length > 0 && selectedImages.size === 0 && (
            <button className="btn btn-outline" onClick={selectAll}>
              全选
            </button>
          )}
          <label className={`btn btn-primary cursor-pointer ${uploading ? 'opacity-50' : ''}`}>
            {uploading ? '上传中...' : '上传图片'}
            <input
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.webp"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      <div className="card bg-amber-50 border-amber-200">
        <h3 className="font-semibold text-amber-900 mb-3">批量导入目录图片</h3>
        <p className="text-sm text-amber-700 mb-4">
          扫描服务器本地目录导入图片（支持最多2000张）
        </p>
        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="服务器路径，例如: /home/ubuntu/images"
            value={directoryPath}
            onChange={(e) => setDirectoryPath(e.target.value)}
            className="input flex-1"
          />
          <button
            className={`btn btn-secondary ${scanning ? 'opacity-50' : ''}`}
            onClick={handleScanDirectory}
            disabled={scanning}
          >
            {scanning ? '扫描中...' : '扫描导入'}
          </button>
        </div>
        <p className="text-xs text-amber-600 mt-2">
          ⚠️ 重要：必须是服务器上的绝对路径（如 /home/ubuntu/xxx），不是您本地电脑路径
        </p>
        <p className="text-xs text-amber-600">
          提示：图片会被复制到系统目录，原文件不会被删除
        </p>
      </div>

      {searchKeyword && (
        <div className="text-sm text-stone-600">
          搜索结果: "{searchKeyword}" - 共 {total} 张图片
          <button
            onClick={() => {
              setSearchKeyword('')
              searchKeywordRef.current = ''
              setPage(1)
            }}
            className="ml-2 text-emerald-600 hover:text-emerald-800 underline"
          >
            清除搜索
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">加载中...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {images.map(image => (
              <div
                key={image.id}
                className={`card p-3 cursor-pointer transition-all hover:shadow-md ${
                  selectedImages.has(image.id) ? 'ring-2 ring-emerald-500' : ''
                }`}
                onClick={() => setSelectedImage(image)}
              >
                <div className="relative aspect-square mb-3 bg-stone-100 rounded-lg overflow-hidden">
                  <img
                    src={imageApi.getFile(image.id)}
                    alt={image.filename}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                  <input
                    type="checkbox"
                    checked={selectedImages.has(image.id)}
                    onChange={(e) => toggleSelect(image.id, e)}
                    className="absolute top-2 left-2 w-5 h-5 rounded border-stone-300"
                  />
                </div>
                
                <p className="text-sm font-medium truncate text-stone-700">{image.filename}</p>
                <div className="flex items-center justify-between mt-2">
                  {getStatusBadge(image.status)}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(image.id)
                    }}
                    className="text-red-500 hover:text-red-700"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2 mt-8">
              <button
                className="btn btn-outline disabled:opacity-50"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                上一页
              </button>
              <span className="text-stone-600">{page} / {totalPages}</span>
              <button
                className="btn btn-outline disabled:opacity-50"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}

      {selectedImage && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div className="bg-white rounded-xl max-w-5xl max-h-[95vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-stone-200 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg">{selectedImage.filename}</h3>
                <p className="text-sm text-stone-500 mt-1">
                  检测到 {selectedImage.detections?.length || 0} 个虫巢
                </p>
              </div>
              <button onClick={() => setSelectedImage(null)} className="text-stone-400 hover:text-stone-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  {selectedImage.detections?.length > 0 ? (
                    <DetectionCanvas
                      imageUrl={imageApi.getFile(selectedImage.id)}
                      detections={selectedImage.detections}
                      width={800}
                      height={600}
                    />
                  ) : (
                    <img
                      src={imageApi.getFile(selectedImage.id)}
                      alt={selectedImage.filename}
                      className="max-w-full max-h-[60vh] object-contain rounded-lg"
                    />
                  )}
                </div>

                {selectedImage.detections?.length > 0 && (
                  <div className="w-full lg:w-64 bg-stone-50 rounded-lg p-4">
                    <h4 className="font-semibold text-stone-700 mb-3">检测详情</h4>
                    <div className="space-y-2 max-h-[500px] overflow-y-auto">
                      {selectedImage.detections.map((det, index) => (
                        <div key={det.id} className="bg-white p-3 rounded border border-stone-200">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">
                              {index + 1}
                            </span>
                            <span className="text-sm font-medium">虫巢 #{index + 1}</span>
                          </div>
                          <div className="text-xs text-stone-600 space-y-1">
                            <div>位置: ({(det.x_center * 100).toFixed(1)}%, {(det.y_center * 100).toFixed(1)}%)</div>
                            <div>大小: {(det.width * 100).toFixed(1)}% x {(det.height * 100).toFixed(1)}%</div>
                            <div className="flex items-center gap-2">
                              <span>严重程度:</span>
                              <span className={`px-2 py-0.5 rounded text-xs ${
                                det.severity === 'light' ? 'bg-yellow-100 text-yellow-800' :
                                det.severity === 'severe' ? 'bg-red-100 text-red-800' :
                                'bg-orange-100 text-orange-800'
                              }`}>
                                {det.severity === 'light' ? '轻微' : det.severity === 'severe' ? '严重' : '中等'}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span>置信度:</span>
                              <span className={`px-2 py-0.5 rounded text-xs ${
                                det.confidence === 'high' ? 'bg-green-100 text-green-800' :
                                det.confidence === 'low' ? 'bg-gray-100 text-gray-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {det.confidence === 'high' ? '高' : det.confidence === 'low' ? '低' : '中'}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 grid grid-cols-4 gap-4 text-sm bg-stone-50 p-4 rounded-lg">
                <div>
                  <span className="text-stone-500">状态: </span>
                  {getStatusBadge(selectedImage.status)}
                </div>
                <div>
                  <span className="text-stone-500">尺寸: </span>
                  {selectedImage.width || '?'} x {selectedImage.height || '?'}
                </div>
                <div>
                  <span className="text-stone-500">文件大小: </span>
                  {selectedImage.file_size ? (selectedImage.file_size / 1024 / 1024).toFixed(2) + ' MB' : '?'}
                </div>
                <div>
                  <span className="text-stone-500">上传时间: </span>
                  {new Date(selectedImage.uploaded_at).toLocaleString('zh-CN')}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Images
