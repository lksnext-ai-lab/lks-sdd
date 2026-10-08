import Link from 'next/link';
import {
  ArrowRight,
  ArrowsLeftRight,
  ArrowsMerge,
  ChatCircleDots,
  CheckCircle,
  CirclesThree,
  ClipboardText,
  Code,
  Eye,
  FileCode,
  GitBranch,
  ImageSquare,
  Lightbulb,
  MagnifyingGlass,
  Path,
  Play,
  ShieldCheck,
  Stack,
  TestTube,
  TreeStructure,
  UserFocus,
  Warning,
} from '@phosphor-icons/react/dist/ssr';
import { EnergyCanvas } from './components/EnergyCanvas';
import { JiraDemo } from './components/JiraDemo';
import { LksLogo } from './components/LksLogo';
import { MendiaraDemo } from './components/MendiaraDemo';
import { OpeningScenes } from './components/OpeningScenes';
import { Reveal } from './components/Reveal';

const skillItems = [
  { name: 'Entender', description: 'Comprende el contexto y los objetivos.', icon: ChatCircleDots },
  { name: 'Definir', description: 'Construye la especificación viva.', icon: ClipboardText },
  { name: 'Adoptar', description: 'Reconcilia un sistema existente.', icon: GitBranch },
  { name: 'Evaluar', description: 'Comprueba preparación y huecos.', icon: MagnifyingGlass },
  { name: 'Implementar', description: 'Ejecuta una tarea autorizada.', icon: Code },
  { name: 'Verificar', description: 'Conecta aceptación y evidencia.', icon: ShieldCheck },
];

const traceItems = [
  ['FR-017', 'Requisito funcional', ClipboardText],
  ['AC-021', 'Criterio de aceptación', CheckCircle],
  ['TASK-008', 'Tarea planificada', TreeStructure],
  ['CODE + TEST', 'Implementación ejecutada', TestTube],
  ['EVID-005', 'Evidencia verificable', ShieldCheck],
] as const;

export default function Home() {
  return (
    <main>
      <EnergyCanvas />

      <header className="site-header">
        <Link href="#inicio" className="brand-link" aria-label="Ir al inicio">
          <LksLogo />
        </Link>
        <nav aria-label="Navegación principal">
          <a href="#vision">Visión</a>
          <a href="#trabajo">Cómo se trabaja</a>
          <a href="#jira">Jira</a>
          <Link href="/por-dentro">Por dentro</Link>
        </nav>
        <a className="header-cta" href="#trabajo">
          Ver el proceso
          <ArrowRight weight="bold" aria-hidden="true" />
        </a>
      </header>

      <OpeningScenes />

      <section className="scene elevate-scene" id="vision">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">03 · ELEVAR</p>
            <h2>Elevar el desarrollo</h2>
          </div>
          <p>
            Más capacidad de ejecución permite dedicar más atención a comprender,
            decidir, priorizar y supervisar.
          </p>
        </Reveal>
        <div className="elevation-stack">
          <Reveal className="elevation-layer layer-supervision" delay={0.18}>
            <span>03</span><ShieldCheck weight="duotone" />
            <div><strong>Supervisión y evidencia</strong><p>Trazabilidad, calidad y cumplimiento.</p></div>
          </Reveal>
          <Reveal className="elevation-layer layer-direction" delay={0.1}>
            <span>02</span><UserFocus weight="duotone" />
            <div><strong>Dirección funcional</strong><p>Alcance, decisiones y priorización.</p></div>
          </Reveal>
          <Reveal className="elevation-layer layer-execution">
            <span>01</span><Code weight="duotone" />
            <div><strong>Ejecución</strong><p>Código, pruebas y entregables.</p></div>
          </Reveal>
        </div>
      </section>

      <section className="scene skills-scene">
        <Reveal className="scene-heading compact-heading">
          <p className="section-index">04 · LA RESPUESTA EN CODEX</p>
          <h2>LKS-SDD guía el trabajo de principio a fin</h2>
          <p>Seis skills conectadas por un mismo contrato vivo.</p>
        </Reveal>
        <div className="skills-line">
          {skillItems.map(({ name, description, icon: Icon }, index) => (
            <Reveal className="skill-step" delay={index * 0.06} key={name}>
              <span className="skill-number">0{index + 1}</span>
              <span className="skill-icon"><Icon weight="duotone" /></span>
              <strong>{name}</strong>
              <p>{description}</p>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="scene scene-dark anchored-scene">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">05 · SPEC-ANCHORED</p>
            <h2>Una spec que no se abandona cuando empieza el código</h2>
          </div>
          <p>
            El enfoque elegido para este plugin mantiene una referencia comprensible
            y contrastable durante toda la evolución.
          </p>
        </Reveal>
        <div className="approach-compare">
          <Reveal className="approach muted-approach">
            <Path /><strong>Spec-first</strong><p>Aclara el inicio, pero puede perder vigencia.</p>
            <span className="approach-path short" />
          </Reveal>
          <Reveal className="approach active-approach" delay={0.08}>
            <ArrowsLeftRight /><strong>Spec-anchored</strong><p>Especificación, código y evidencia evolucionan conectados.</p>
            <span className="approach-path continuous" />
          </Reveal>
          <Reveal className="approach muted-approach" delay={0.16}>
            <CirclesThree /><strong>Spec-as-source</strong><p>La especificación intenta ser el origen ejecutable de todo.</p>
            <span className="approach-path spiral" />
          </Reveal>
        </div>
        <p className="boundary-note">Es una decisión de diseño del plugin, no una metodología corporativa aprobada para toda LKS Next.</p>
      </section>

      <section className="scene scene-dark living-spec-scene">
        <Reveal className="scene-heading compact-heading">
          <p className="section-index">06 · CONTRATO VIVO</p>
          <h2>La spec evoluciona con el producto</h2>
          <p>No se termina antes de desarrollar. Se amplía y reconcilia según cambia el producto.</p>
        </Reveal>
        <Reveal className="spec-orbit">
          <div className="orbit-center">
            <Stack weight="duotone" />
            <strong>Especificación viva</strong>
            <small>v1.0 → v1.1</small>
          </div>
          <div className="orbit-node node-a"><ClipboardText />Especificación</div>
          <div className="orbit-node node-b"><Lightbulb />Cambio funcional</div>
          <div className="orbit-node node-c"><Code />Código + pruebas</div>
          <div className="orbit-node node-d"><ShieldCheck />Evidencia</div>
          <div className="orbit-node node-e"><ArrowsMerge />Reconciliación</div>
          <div className="human-gate"><UserFocus weight="fill" />Confirmación humana</div>
        </Reveal>
      </section>

      <section className="scene entrances-scene">
        <Reveal className="scene-heading compact-heading">
          <p className="section-index">07 · DOS PUERTAS</p>
          <h2>Dos formas de empezar. Un contrato vivo.</h2>
          <p>El punto de partida cambia; la disciplina de evolución es la misma.</p>
        </Reveal>
        <div className="entry-paths">
          <Reveal className="entry-path new-entry">
            <span className="entry-label">Proyecto nuevo</span>
            <div className="entry-visual"><Lightbulb /><ArrowRight /><ChatCircleDots /><ArrowRight /><ClipboardText /></div>
            <strong>De la intención confirmada a la primera especificación</strong>
          </Reveal>
          <div className="entry-contract"><Stack weight="duotone" /><strong>Spec viva</strong></div>
          <Reveal className="entry-path existing-entry" delay={0.1}>
            <span className="entry-label">Proyecto existente</span>
            <div className="entry-visual"><FileCode /><ArrowRight /><Eye /><ArrowRight /><GitBranch /></div>
            <strong>Del código observado a una baseline documental progresiva</strong>
          </Reveal>
        </div>
        <Reveal className="entry-statement">
          El código muestra lo que existe. <strong>Las personas confirman</strong> qué debe conservarse, cambiar o incorporarse.
        </Reveal>
      </section>

      <section className="scene conversation-scene" id="trabajo">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">08 · CONVERSACIÓN FUNCIONAL</p>
            <h2>Todo empieza con una conversación</h2>
          </div>
          <p>
            Para el caso ficticio Mendiara Mobility, cada aportación relevante
            abandona el chat y ocupa su lugar en la definición.
          </p>
        </Reveal>
        <div className="conversation-layout">
          <Reveal className="functional-chat">
            <div className="chat-head"><ChatCircleDots weight="duotone" />CODEX · LKS-SDD</div>
            <div className="message message-user">Necesitamos gestionar vehículos, rutas e incidencias desde una única aplicación.</div>
            <div className="message message-codex">¿Qué reglas deben mantenerse y quién toma cada decisión operativa?</div>
            <div className="message message-user">Las incidencias críticas deben priorizarse y quedar trazadas.</div>
          </Reveal>
          <div className="classified-notes">
            <Reveal className="classified-note fact" delay={0.04}><span>Hecho</span>Existe una flota distribuida por bases.</Reveal>
            <Reveal className="classified-note proposal" delay={0.1}><span>Propuesta</span>Vista única de flota, rutas e incidencias.</Reveal>
            <Reveal className="classified-note decision" delay={0.16}><span>Decisión</span>Priorizar incidencias por impacto.</Reveal>
            <Reveal className="classified-note pending" delay={0.22}><span>Pendiente</span>Integración posterior con telemetría.</Reveal>
          </div>
        </div>
      </section>

      <section className="scene proposal-scene">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">09 · PROPONER Y VISUALIZAR</p>
            <h2>Comparar antes de construir</h2>
          </div>
          <p>Codex propone alternativas técnicas y visuales. La persona contrasta, selecciona y afina.</p>
        </Reveal>
        <div className="proposal-grid">
          <Reveal className="technical-options">
            <article><span>Opción A</span><strong>Monolito modular</strong><small>Menor complejidad inicial · evolución controlada</small></article>
            <article className="selected"><span>Opción B · seleccionada</span><strong>Modular por dominio</strong><small>Separación funcional · crecimiento progresivo</small></article>
          </Reveal>
          <Reveal className="visual-options" delay={0.12}>
            <div className="prototype-card"><ImageSquare /><span>Operaciones</span></div>
            <div className="prototype-card selected"><ImageSquare weight="fill" /><span>Flota</span></div>
            <div className="prototype-card"><ImageSquare /><span>Incidencias</span></div>
            <div className="prototype-refined">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/assets/mendiara-fleet.png" alt="Fotografía corporativa ficticia de Mendiara Mobility" />
              <span>Propuesta afinada</span>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="scene scene-dark authorization-scene">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">10 · PLANIFICAR Y AUTORIZAR</p>
            <h2>Proponer no es ejecutar</h2>
          </div>
          <p>Alcance, aceptación, tareas y dependencias convergen antes de abrir una autorización delimitada.</p>
        </Reveal>
        <div className="authorization-flow">
          <span><ClipboardText />FR + AC</span><ArrowRight />
          <span><TreeStructure />PLAN + TASK</span><ArrowRight />
          <span><MagnifyingGlass />READINESS</span><ArrowRight />
          <strong><UserFocus weight="fill" />AUTORIZAR</strong><ArrowRight />
          <span><Play weight="fill" />EJECUTAR</span>
        </div>
        <p className="authorization-note"><Warning weight="fill" /> Una evaluación de readiness nunca autoriza por sí sola la implementación.</p>
      </section>

      <section className="scene mendiara-scene">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">11 · EJECUCIÓN Y REVISIÓN</p>
            <h2>Creando una aplicación con Codex</h2>
          </div>
          <p>De la conversación funcional a una web UI alineada con la imagen corporativa del cliente.</p>
        </Reveal>
        <Reveal><MendiaraDemo /></Reveal>
      </section>

      <section className="scene scene-dark trace-scene">
        <Reveal className="scene-heading compact-heading">
          <p className="section-index">12 · TRAZABILIDAD</p>
          <h2>Del requisito a la evidencia</h2>
          <p>Cada paso conserva su relación. Código escrito y código verificado siguen siendo hechos distintos.</p>
        </Reveal>
        <div className="trace-line">
          {traceItems.map(([id, label, Icon], index) => (
            <Reveal className="trace-step" delay={index * 0.07} key={id}>
              <span><Icon weight="duotone" /></span>
              <strong>{id}</strong>
              <small>{label}</small>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="scene jira-scene" id="jira">
        <Reveal className="scene-heading split-heading">
          <div>
            <p className="section-index">13 · PROYECCIÓN OPERATIVA</p>
            <h2>Integración con Jira</h2>
          </div>
          <p>Las tareas y los hitos pueden proyectarse en Jira sin sacar la fuente de verdad del repositorio.</p>
        </Reveal>
        <Reveal><JiraDemo /></Reveal>
        <p className="jira-boundary"><ShieldCheck weight="duotone" />Jira es una proyección operativa. No autoriza, no verifica y no sustituye el contrato del repositorio.</p>
      </section>

      <section className="final-scene">
        <div className="final-flow" aria-hidden="true"><span /><span /><span /></div>
        <Reveal>
          <p className="section-index">14 · SIGUIENTE NIVEL</p>
          <h2>Acelerar<br />sin perder<br />el control</h2>
          <p>Especificaciones vivas, decisiones humanas y ejecución verificable dentro de Codex.</p>
          <div className="final-actions">
            <Link className="primary-action" href="/por-dentro">Ver el plugin por dentro <ArrowRight weight="bold" /></Link>
            <a className="secondary-action" href="#trabajo">Volver al proceso</a>
          </div>
        </Reveal>
      </section>
    </main>
  );
}
