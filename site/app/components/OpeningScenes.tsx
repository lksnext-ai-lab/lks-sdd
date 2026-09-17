'use client';

import { useEffect, useRef, useState } from 'react';
import {
  ArrowDown,
  ArrowRight,
  BracketsCurly,
  CheckCircle,
  ClipboardText,
  Code,
  Lightbulb,
  ShieldCheck,
  TestTube,
  UserFocus,
} from '@phosphor-icons/react';

const fragments = [
  { label: 'Necesidad', icon: Lightbulb, className: 'fragment-need', dx: -180, dy: -80, rotate: -12 },
  { label: 'Requisito', icon: ClipboardText, className: 'fragment-requirement', dx: -130, dy: 110, rotate: 9 },
  { label: 'Decisión', icon: UserFocus, className: 'fragment-decision', dx: -80, dy: -140, rotate: -7 },
  { label: 'Código', icon: BracketsCurly, className: 'fragment-code', dx: 110, dy: -130, rotate: 8 },
  { label: 'Prueba', icon: TestTube, className: 'fragment-test', dx: 150, dy: 95, rotate: -9 },
  { label: 'Evidencia', icon: ShieldCheck, className: 'fragment-evidence', dx: 210, dy: -45, rotate: 12 },
] as const;

const clamp = (value: number) => Math.min(1, Math.max(0, value));

export function OpeningScenes() {
  const heroRef = useRef<HTMLElement>(null);
  const challengeRef = useRef<HTMLElement>(null);
  const challengeStickyRef = useRef<HTMLDivElement>(null);
  const [heroProgress, setHeroProgress] = useState(0);

  useEffect(() => {
    let frame = 0;
    const sticky = challengeStickyRef.current;
    const fragmentNodes = sticky
      ? Array.from(sticky.querySelectorAll<HTMLElement>('.opening-fragment'))
      : [];

    const update = () => {
      frame = 0;
      const viewport = window.innerHeight;
      const hero = heroRef.current?.getBoundingClientRect();
      const challenge = challengeRef.current?.getBoundingClientRect();

      if (hero) {
        setHeroProgress(clamp(-hero.top / Math.max(hero.height * 0.62, 1)));
      }

      if (challenge && sticky) {
        const entry = clamp((viewport - challenge.top) / viewport);
        const stickyTravel = Math.max(challenge.height - viewport, 1);
        const sectionTravel = clamp(-challenge.top / stickyTravel);
        const exitWindow = viewport * 0.72;
        const exitStart = Math.max(stickyTravel - exitWindow, 0);
        const exit = clamp((-challenge.top - exitStart) / Math.max(exitWindow, 1));
        const copyReveal = clamp((entry - 0.2) / 0.45);
        const assembly = clamp((entry - 0.3) / 0.58);
        const resolutionReveal = clamp((entry - 0.58) / 0.34);
        const activeOpacity = 1 - exit;

        sticky.style.setProperty('--entry-wipe-x', `${entry * 112}%`);
        sticky.style.setProperty('--copy-opacity', `${copyReveal * activeOpacity}`);
        sticky.style.setProperty('--copy-x', `${(1 - copyReveal) * -72}px`);
        sticky.style.setProperty('--copy-y', `${exit * -42}px`);
        sticky.style.setProperty('--scene-image-scale', `${1.13 - entry * 0.08 + exit * 0.17}`);
        sticky.style.setProperty('--scene-image-x', `${exit * -3.8}%`);
        sticky.style.setProperty('--scene-image-brightness', `${0.72 + entry * 0.28 - exit * 0.13}`);
        sticky.style.setProperty('--signal-opacity', `${clamp((entry - 0.42) / 0.3) * activeOpacity}`);
        sticky.style.setProperty('--signal-scale', `${0.72 + assembly * 0.28 + exit * 1.7}`);
        sticky.style.setProperty('--resolution-opacity', `${resolutionReveal * activeOpacity}`);
        sticky.style.setProperty('--resolution-x', `${(1 - resolutionReveal) * 94 + exit * 170}px`);
        sticky.style.setProperty('--sequence-opacity', `${clamp((entry - 0.68) / 0.26) * activeOpacity}`);
        sticky.style.setProperty('--sequence-scale', `${clamp((entry - 0.62) / 0.3)}`);
        sticky.style.setProperty('--exit-left', `${106 - exit * 106}%`);
        sticky.style.setProperty('--exit-right', `${128 - exit * 128}%`);
        sticky.style.setProperty('--chapter-progress', `${sectionTravel * 100}%`);

        fragmentNodes.forEach((node, index) => {
          const fragment = fragments[index];
          const departureDirection = index < 3 ? -1 : 1;
          const departureLift = index % 2 === 0 ? -1 : 1;
          const translateX = fragment.dx * (1 - assembly) + departureDirection * exit * (120 + index * 18);
          const translateY = fragment.dy * (1 - assembly) + departureLift * exit * 86;
          const rotation = fragment.rotate * (1 - assembly) + departureDirection * exit * 10;
          const opacity = (0.16 + assembly * 0.84) * activeOpacity;

          node.style.opacity = `${opacity}`;
          node.style.transform = `translate3d(${translateX}px, ${translateY}px, 0) rotate(${rotation}deg)`;
        });
      }
    };

    const requestUpdate = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };

    update();
    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', requestUpdate);

    return () => {
      window.removeEventListener('scroll', requestUpdate);
      window.removeEventListener('resize', requestUpdate);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  const heroImageStyle = {
    transform: `translate3d(${heroProgress * -2.2}%, ${heroProgress * 1.5}%, 0) scale(${1.015 + heroProgress * 0.045})`,
  };

  return (
    <>
      <section className="opening-hero" id="inicio" ref={heroRef}>
        <div className="opening-hero__visual" aria-hidden="true">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/assets/hero-spec-to-app.png" alt="" style={heroImageStyle} />
        </div>
        <div className="opening-hero__wash" aria-hidden="true" />
        <div className="opening-hero__copy">
          <p className="opening-kicker">
            <span>01</span>
            LKS-SDD · SPEC-ANCHORED
          </p>
          <h1>
            <span>Desarrollo SDD</span>
            <span>con CODEX</span>
          </h1>
          <p className="opening-hero__lede">
            Un plugin de LKS Next para CODEX que convierte las especificaciones
            en un contrato vivo para dirigir, implementar y verificar el desarrollo.
          </p>
          <a className="opening-scroll-cue" href="#reto">
            <span><ArrowDown aria-hidden="true" /></span>
            Explorar el enfoque
          </a>
        </div>

        <div className="opening-hero__stages" aria-label="Etapas que conecta LKS-SDD">
          <article className="opening-stage stage-direct">
            <UserFocus weight="duotone" aria-hidden="true" />
            <span>01</span>
            <strong>Dirigir</strong>
            <small>Intención y decisiones</small>
          </article>
          <article className="opening-stage stage-build">
            <Code weight="duotone" aria-hidden="true" />
            <span>02</span>
            <strong>Implementar</strong>
            <small>Código y pruebas</small>
          </article>
          <article className="opening-stage stage-verify">
            <CheckCircle weight="duotone" aria-hidden="true" />
            <span>03</span>
            <strong>Verificar</strong>
            <small>Aceptación y evidencia</small>
          </article>
        </div>

        <span className="opening-hero__edge" aria-hidden="true">CONTRATO VIVO · 01</span>
      </section>

      <section className="opening-challenge" id="reto" ref={challengeRef}>
        <div className="opening-challenge__sticky" ref={challengeStickyRef}>
          <div className="opening-challenge__visual" aria-hidden="true">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/assets/challenge-convergence.png" alt="" />
          </div>
          <div className="opening-challenge__shade" aria-hidden="true" />
          <div className="opening-challenge__entry-wipe" aria-hidden="true" />

          <div className="opening-challenge__copy">
            <p className="opening-kicker opening-kicker--dark">
              <span>02</span>
              EL RETO
            </p>
            <h2>Cuando la ejecución avanza más rápido</h2>
            <p>
              El reto es mantener conectadas la intención, las decisiones, el código,
              las pruebas y las evidencias mientras aumenta la capacidad de ejecución.
            </p>
          </div>

          <div className="opening-fragments" aria-label="Elementos que deben permanecer conectados">
            {fragments.map(({ label, icon: Icon, className }) => (
              <article className={`opening-fragment ${className}`} key={label}>
                <Icon weight="duotone" aria-hidden="true" />
                <span>{label}</span>
              </article>
            ))}
          </div>

          <div className="opening-challenge__signal" aria-hidden="true">
            <span />
          </div>

          <div className="opening-challenge__resolution">
            <span>Más ejecución</span>
            <ArrowRight aria-hidden="true" />
            <strong>Más dirección y supervisión</strong>
          </div>

          <div className="opening-challenge__sequence" aria-label="Cadena de control">
            <span>Intención</span><i />
            <span>Decisión</span><i />
            <span>Ejecución</span><i />
            <span>Evidencia</span>
          </div>

          <div className="opening-challenge__chapter" aria-hidden="true">
            <span>02</span>
            <i><b /></i>
            <span>03</span>
          </div>

          <div className="opening-challenge__exit-wipe" aria-hidden="true">
            <span>03</span>
            <p>Elevar el desarrollo</p>
          </div>
        </div>
      </section>
    </>
  );
}
