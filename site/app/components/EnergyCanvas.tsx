'use client';

import { useEffect, useRef } from 'react';

export function EnergyCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let cancelled = false;
    let cleanup = () => {};

    void (async () => {
      const THREE = await import('three');
      if (cancelled || !canvasRef.current) return;

      const canvas = canvasRef.current;
      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
      renderer.setClearColor(0x000000, 0);

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 100);
      camera.position.set(0, 0, 8.5);

      const group = new THREE.Group();
      scene.add(group);

      const controlPoints = [
        new THREE.Vector3(-5.2, -0.7, 0),
        new THREE.Vector3(-2.8, 1.3, 0.4),
        new THREE.Vector3(-0.4, -0.25, -0.2),
        new THREE.Vector3(2.2, 1.1, 0.5),
        new THREE.Vector3(5.4, -0.35, 0),
      ];
      const curve = new THREE.CatmullRomCurve3(controlPoints);
      const lineGeometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(180));
      const lineMaterial = new THREE.LineBasicMaterial({
        color: 0xff5a00,
        transparent: true,
        opacity: 0.42,
        blending: THREE.AdditiveBlending,
      });
      const line = new THREE.Line(lineGeometry, lineMaterial);
      group.add(line);

      const particleCount = 260;
      const positions = new Float32Array(particleCount * 3);
      const seeds = new Float32Array(particleCount);
      for (let index = 0; index < particleCount; index += 1) {
        const t = index / particleCount;
        const point = curve.getPoint(t);
        positions[index * 3] = point.x + (Math.random() - 0.5) * 0.55;
        positions[index * 3 + 1] = point.y + (Math.random() - 0.5) * 0.55;
        positions[index * 3 + 2] = point.z + (Math.random() - 0.5) * 0.75;
        seeds[index] = Math.random() * Math.PI * 2;
      }
      const particleGeometry = new THREE.BufferGeometry();
      particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const particleMaterial = new THREE.PointsMaterial({
        color: 0xff6a14,
        size: 0.045,
        transparent: true,
        opacity: 0.72,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      const particles = new THREE.Points(particleGeometry, particleMaterial);
      group.add(particles);

      let frame = 0;
      let scrollRatio = 0;
      let active = !document.hidden;
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      const resize = () => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      };
      const onScroll = () => {
        const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
        scrollRatio = window.scrollY / max;
      };
      const onVisibility = () => { active = !document.hidden; };

      const render = (time: number) => {
        if (active) {
          if (!reduced) {
            group.rotation.z = scrollRatio * Math.PI * 1.9;
            group.rotation.y = Math.sin(scrollRatio * Math.PI * 3) * 0.18;
            particles.rotation.x = Math.sin(time * 0.00018) * 0.08;
            const attribute = particleGeometry.getAttribute('position');
            for (let index = 0; index < particleCount; index += 1) {
              const y = index * 3 + 1;
              attribute.array[y] += Math.sin(time * 0.0012 + seeds[index]) * 0.00045;
            }
            attribute.needsUpdate = true;
          }
          renderer.render(scene, camera);
        }
        frame = window.requestAnimationFrame(render);
      };

      resize();
      onScroll();
      window.addEventListener('resize', resize);
      window.addEventListener('scroll', onScroll, { passive: true });
      document.addEventListener('visibilitychange', onVisibility);
      frame = window.requestAnimationFrame(render);

      cleanup = () => {
        window.cancelAnimationFrame(frame);
        window.removeEventListener('resize', resize);
        window.removeEventListener('scroll', onScroll);
        document.removeEventListener('visibilitychange', onVisibility);
        lineGeometry.dispose();
        lineMaterial.dispose();
        particleGeometry.dispose();
        particleMaterial.dispose();
        renderer.dispose();
      };
    })();

    return () => {
      cancelled = true;
      cleanup();
    };
  }, []);

  return <canvas ref={canvasRef} className="energy-canvas" aria-hidden="true" />;
}
