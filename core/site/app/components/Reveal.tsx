'use client';

import { useEffect, useRef, useState, type CSSProperties, type PropsWithChildren } from 'react';

type RevealProps = PropsWithChildren<{
  className?: string;
  delay?: number;
}>;

export function Reveal({ children, className, delay = 0 }: RevealProps) {
  const elementRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12 },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={elementRef}
      className={`${className ?? ''} reveal${visible ? ' is-visible' : ''}`.trim()}
      style={{ '--reveal-delay': `${delay}s` } as CSSProperties}
    >
      {children}
    </div>
  );
}
