import { useEffect, useRef } from 'react'

interface AnimatedGradientMeshProps {
  className?: string
  colors?: string[]
}

export default function AnimatedGradientMesh({
  className = '',
  colors = ['#2563EB', '#06B6D4', '#14B8A6', '#10B981']
}: AnimatedGradientMeshProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Set canvas size
    const setCanvasSize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    setCanvasSize()
    window.addEventListener('resize', setCanvasSize)

    // Gradient blob class
    class GradientBlob {
      x: number
      y: number
      radius: number
      vx: number
      vy: number
      color: string

      constructor(x: number, y: number, radius: number, color: string) {
        this.x = x
        this.y = y
        this.radius = radius
        this.vx = (Math.random() - 0.5) * 0.5
        this.vy = (Math.random() - 0.5) * 0.5
        this.color = color
      }

      update(width: number, height: number) {
        this.x += this.vx
        this.y += this.vy

        if (this.x < 0 || this.x > width) this.vx *= -1
        if (this.y < 0 || this.y > height) this.vy *= -1
      }

      draw(ctx: CanvasRenderingContext2D) {
        const gradient = ctx.createRadialGradient(
          this.x,
          this.y,
          0,
          this.x,
          this.y,
          this.radius
        )
        gradient.addColorStop(0, this.color + '80')
        gradient.addColorStop(1, this.color + '00')

        ctx.fillStyle = gradient
        ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height)
      }
    }

    // Create blobs
    const blobs = colors.map((color, i) => {
      const x = (canvas.width / (colors.length + 1)) * (i + 1)
      const y = canvas.height / 2
      const radius = Math.min(canvas.width, canvas.height) * 0.4
      return new GradientBlob(x, y, radius, color)
    })

    // Animation loop
    let animationId: number

    const animate = () => {
      if (!ctx || !canvas) return

      // Clear canvas
      ctx.fillStyle = '#0A1628'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Update and draw blobs
      if (!prefersReducedMotion) {
        blobs.forEach(blob => {
          blob.update(canvas.width, canvas.height)
          blob.draw(ctx)
        })
      } else {
        // Static blobs if reduced motion
        blobs.forEach(blob => {
          blob.draw(ctx)
        })
      }

      // Apply blur effect
      ctx.filter = 'blur(60px)'
      ctx.drawImage(canvas, 0, 0)
      ctx.filter = 'none'

      animationId = requestAnimationFrame(animate)
    }

    animate()

    // Cleanup
    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', setCanvasSize)
    }
  }, [colors])

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 ${className}`}
      style={{ opacity: 0.3 }}
    />
  )
}
