import { useState, useEffect, RefObject } from 'react';
import { useReducedMotion } from './useReducedMotion';

interface ParallaxOptions {
  speed?: number; // Multiplier for parallax effect (0.1 = subtle, 0.3 = strong)
  direction?: 'vertical' | 'horizontal' | 'both';
}

interface ParallaxValues {
  x: number;
  y: number;
}

/**
 * Hook to create parallax scroll effects
 * Returns transform values based on scroll position
 * Respects reduced motion preference
 */
export function useParallax(
  ref: RefObject<HTMLElement>,
  options: ParallaxOptions = {}
): ParallaxValues {
  const { speed = 0.2, direction = 'vertical' } = options;
  const prefersReducedMotion = useReducedMotion();
  const [parallaxValues, setParallaxValues] = useState<ParallaxValues>({
    x: 0,
    y: 0,
  });

  useEffect(() => {
    if (prefersReducedMotion) {
      setParallaxValues({ x: 0, y: 0 });
      return;
    }

    const handleScroll = () => {
      if (!ref.current) return;

      const rect = ref.current.getBoundingClientRect();
      const scrollProgress = 1 - (rect.top + rect.height / 2) / window.innerHeight;

      const yOffset = direction !== 'horizontal' ? scrollProgress * speed * 100 : 0;
      const xOffset = direction !== 'vertical' ? scrollProgress * speed * 100 : 0;

      setParallaxValues({
        x: xOffset,
        y: yOffset,
      });
    };

    handleScroll(); // Initial calculation
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [ref, speed, direction, prefersReducedMotion]);

  return parallaxValues;
}
