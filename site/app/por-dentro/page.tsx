import Link from 'next/link';
import {
  ArrowLeft,
  ArrowRight,
  BracketsCurly,
  ChatCircleDots,
  CheckCircle,
  ClipboardText,
  Code,
  FileMd,
  FolderOpen,
  GearSix,
  ImageSquare,
  Kanban,
  LockKey,
  ShieldCheck,
  TreeStructure,
} from '@phosphor-icons/react/dist/ssr';
import { EnergyCanvas } from '../components/EnergyCanvas';
import { LksLogo } from '../components/LksLogo';
import { Reveal } from '../components/Reveal';
import { TechLayers } from '../components/TechLayers';

const skills = [
  ['Ayudar', 'Orientar sin modificar', ChatCircleDots],
  ['Definir', 'Descubrir y especificar', ClipboardText],
  ['Adoptar', 'Reconstruir una baseline', FolderOpen],
  ['Evaluar', 'Comprobar readiness', CheckCircle],
  ['Implementar', 'Ejecutar una TASK autorizada', Code],
  ['Verificar', 'Vincular aceptación y evidencia', ShieldCheck],
] as const;

export default function InsidePage() {
  return (
    <main className="inside-page">
      <EnergyCanvas />
      <header className="site-header inside-header">
        <Link href="/" aria-label="Volver a la visión"><LksLogo /></Link>
        <nav aria-label="Navegación técnica">
          <Link href="/">Visión</Link>
          <Link href="/#trabajo">Cómo se trabaja</Link>
          <span className="active-nav">Por dentro</span>
        </nav>
        <Link className="header-cta" href="/"><ArrowLeft /> Volver</Link>
      </header>

      <section className="inside-hero">
        <Reveal className="inside-copy">
          <p className="eyebrow"><span />LKS-SDD · ARQUITECTURA</p>
          <h1>Por dentro<br />de LKS-SDD</h1>
          <p>Un plugin skills-only para Codex. Método, contratos y gates aplicados sobre el repositorio de cada proyecto.</p>
          <strong>La verdad semántica vive en Markdown versionado.</strong>
        </Reveal>
        <Reveal className="inside-layer-stage" delay={0.1}><TechLayers /></Reveal>
      </section>

      <section className="tech-section tech-skills">
        <Reveal className="scene-heading compact-heading">
          <p className="section-index">02 · WORKFLOWS DESCUBRIBLES</p>
          <h2>Seis skills. Seis responsabilidades.</h2>
          <p>La invocación puede ser explícita o implícita, pero sus límites no se solapan.</p>
        </Reveal>
        <div className="tech-skill-list">
          {skills.map(([title, copy, Icon], index) => (
            <Reveal className="tech-skill-row" delay={index * .05} key={title}>
              <span>0{index + 1}</span><Icon weight="duotone" /><strong>{title}</strong><p>{copy}</p>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="tech-section tech-contract">
        <Reveal className="scene-heading split-heading">
          <div><p className="section-index">03 · MOTOR CONTRACTUAL</p><h2>El método se puede comprobar</h2></div>
          <p>Plantillas, schemas y motores convierten el contrato documental en estados y gates verificables.</p>
        </Reveal>
        <div className="contract-engine">
          <Reveal className="engine-column"><FileMd /><strong>Markdown</strong><span>Intención · requisitos · decisiones</span></Reveal>
          <ArrowRight className="engine-arrow" />
          <Reveal className="engine-column" delay={.06}><BracketsCurly /><strong>Schemas</strong><span>Estructura · IDs · referencias</span></Reveal>
          <ArrowRight className="engine-arrow" />
          <Reveal className="engine-column active" delay={.12}><GearSix /><strong>Motores</strong><span>Planning · tracking · continuidad</span></Reveal>
          <ArrowRight className="engine-arrow" />
          <Reveal className="engine-column" delay={.18}><ShieldCheck /><strong>Gates</strong><span>Readiness · verificación · evidencia</span></Reveal>
        </div>
      </section>

      <section className="tech-section repo-section">
        <Reveal className="scene-heading split-heading">
          <div><p className="section-index">04 · REPOSITORIO CONSUMIDOR</p><h2>La autoridad permanece en el proyecto</h2></div>
          <p>El plugin aplica el método. El repositorio conserva documentación, código, estado y evidencia.</p>
        </Reveal>
        <div className="repo-layout">
          <Reveal className="repo-tree">
            <div><FolderOpen weight="fill" />docs/lks-sdd <b>FUENTE DE VERDAD</b></div>
            <span><FileMd />01-context/</span>
            <span><FileMd />02-requirements/</span>
            <span><FileMd />03-solution/</span>
            <span><TreeStructure />04-delivery/</span>
            <span><ShieldCheck />05-quality/</span>
            <div><FolderOpen weight="fill" />src + tests</div>
            <div><FolderOpen weight="fill" />evidencias + checkpoints</div>
            <div><BracketsCurly />.lks-sdd/project.json <small>ÍNDICE</small></div>
          </Reveal>
          <Reveal className="continuity-demo" delay={.1}>
            <span>AUTH-004</span><span>EXEC-008</span><span>CKPT-012</span>
            <div><LockKey weight="duotone" /><strong>Pausar y reanudar sin depender del chat</strong></div>
          </Reveal>
        </div>
      </section>

      <section className="tech-section gates-section">
        <Reveal className="scene-heading compact-heading">
          <p className="section-index">05 · GATES Y LÍMITES</p>
          <h2>Automatización con fronteras visibles</h2>
          <p>El sistema acelera la ejecución sin asumir la autoridad de las personas ni de los sistemas externos.</p>
        </Reveal>
        <div className="gate-track">
          <Reveal><span>G2</span><strong>READY</strong><small>Preparación y autorización aplicable</small></Reveal>
          <Reveal delay={.08}><span>G3</span><strong>VERIFICAR</strong><small>Gates técnicos ejecutados</small></Reveal>
          <Reveal delay={.16}><span>G4</span><strong>EVIDENCIA</strong><small>Entrega y promoción verificables</small></Reveal>
        </div>
        <div className="external-peers">
          <article><ImageSquare weight="duotone" /><strong>ImageGen</strong><span>Capacidad opcional</span><small>Peer externo</small></article>
          <article><Kanban weight="duotone" /><strong>Atlassian Rovo / Jira</strong><span>Proyección opcional</span><small>Peer externo</small></article>
        </div>
        <p className="limits-line">Skills-only · Sin MCP, hooks, app o cliente Jira propios · Ninguna propuesta equivale a aprobación</p>
        <Link className="primary-action light-action" href="/">Volver a la visión <ArrowRight weight="bold" /></Link>
      </section>
    </main>
  );
}
