import React, { useRef, useEffect, useState } from 'react'

function DetectionCanvas({ imageUrl, detections, width = 800, height = 600, onBoxClick }) {
  const canvasRef = useRef(null)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 })
  const [hoveredBox, setHoveredBox] = useState(null)

  useEffect(() => {
    const img = new Image()
    img.onload = () => {
      setImageSize({ width: img.width, height: img.height })
      setImageLoaded(true)
    }
    img.src = imageUrl
  }, [imageUrl])

  useEffect(() => {
    if (!imageLoaded || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const img = new Image()

    img.onload = () => {
      const scale = Math.min(width / img.width, height / img.height)
      const drawWidth = img.width * scale
      const drawHeight = img.height * scale
      const offsetX = (width - drawWidth) / 2
      const offsetY = (height - drawHeight) / 2

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)

      detections?.forEach((det, index) => {
        const { x_center, y_center, width: boxWidth, height: boxHeight, severity, confidence } = det

        const x = offsetX + x_center * drawWidth
        const y = offsetY + y_center * drawHeight
        const w = boxWidth * drawWidth
        const h = boxHeight * drawHeight
        const x1 = x - w / 2
        const y1 = y - h / 2

        let color = '#ff4444'
        if (severity === 'light') color = '#ffaa00'
        if (severity === 'severe') color = '#cc0000'

        if (hoveredBox === index) {
          color = '#00ff00'
        }

        ctx.strokeStyle = color
        ctx.lineWidth = 3
        ctx.strokeRect(x1, y1, w, h)

        ctx.fillStyle = color + '20'
        ctx.fillRect(x1, y1, w, h)

        ctx.fillStyle = color
        ctx.font = 'bold 14px Arial'
        ctx.textBaseline = 'top'
        const label = `${severity} | ${confidence}`
        const textMetrics = ctx.measureText(label)
        ctx.fillRect(x1, y1 - 20, textMetrics.width + 10, 20)
        ctx.fillStyle = '#ffffff'
        ctx.fillText(label, x1 + 5, y1 - 18)

        ctx.fillStyle = color
        ctx.font = 'bold 16px Arial'
        ctx.fillText((index + 1).toString(), x1 + 5, y1 + 5)
      })

      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
      ctx.fillRect(10, 10, 200, 60)
      ctx.fillStyle = '#ffffff'
      ctx.font = '14px Arial'
      ctx.fillText(`检测到 ${detections?.length || 0} 个虫巢`, 20, 30)
      ctx.fillText(`图片尺寸: ${img.width} x ${img.height}`, 20, 50)
    }

    img.src = imageUrl
  }, [imageLoaded, detections, width, height, hoveredBox])

  const handleMouseMove = (e) => {
    if (!canvasRef.current || !imageSize.width) return

    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const scale = Math.min(width / imageSize.width, height / imageSize.height)
    const drawWidth = imageSize.width * scale
    const drawHeight = imageSize.height * scale
    const offsetX = (width - drawWidth) / 2
    const offsetY = (height - drawHeight) / 2

    let found = null
    detections?.forEach((det, index) => {
      const boxX = offsetX + det.x_center * drawWidth
      const boxY = offsetY + det.y_center * drawHeight
      const boxW = det.width * drawWidth
      const boxH = det.height * drawHeight
      const x1 = boxX - boxW / 2
      const y1 = boxY - boxH / 2
      const x2 = x1 + boxW
      const y2 = y1 + boxH

      if (x >= x1 && x <= x2 && y >= y1 && y <= y2) {
        found = index
      }
    })

    setHoveredBox(found)
    canvas.style.cursor = found !== null ? 'pointer' : 'default'
  }

  const handleClick = (e) => {
    if (hoveredBox !== null && onBoxClick) {
      onBoxClick(detections[hoveredBox], hoveredBox)
    }
  }

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      onMouseMove={handleMouseMove}
      onClick={handleClick}
      className="border rounded-lg shadow-lg"
      style={{ maxWidth: '100%', height: 'auto' }}
    />
  )
}

export default DetectionCanvas
