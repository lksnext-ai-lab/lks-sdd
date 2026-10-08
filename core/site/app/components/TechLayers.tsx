'use client';

import { useState, type CSSProperties } from 'react';
import {
  BracketsCurly,
  ChatCircleDots,
  CheckCircle,
  ClipboardText,
  Code,
  FolderOpen,
  GearSix,
  ShieldCheck,
  Stack,
  TreeStructure,
} from '@phosphor-icons/react';

const layers = [
  { title: 'Codex · intención', description: 'Comprende la petición y activa la capacidad adecuada.', icon: ChatCircleDots },
  { title: '6 skills', description: 'Ayudar, definir, adoptar, evaluar, implementar y verificar.', icon: GearSix },
  { title: 'Método + plantillas', description: 'Convierte conversación y decisiones en documentación utilizable.', icon: ClipboardText },
  { title: 'Contratos + schemas', description: 'Valida estructura, estados, referencias y trazabilidad.', icon: BracketsCurly },
  { title: 'Perfiles + gates', description: 'Liga cada unidad a una pila exacta y sus comprobaciones.', icon: ShieldCheck },
  { title: 'Repositorio del proyecto', description: 'Conserva especificaciones, código, pruebas y evidencia.', icon: FolderOpen },
];

export function TechLayers() {
  const [active, setActive] = useState(3);

  return (
    <div className="tech-layers">
      <div className="layer-stack" role="tablist" aria-label="Capas del plugin">
        {layers.map(({ title, icon: Icon }, index) => (
          <button
            type="button"
            role="tab"
            aria-selected={active === index}
            className={active === index ? 'active' : ''}
            key={title}
            onClick={() => setActive(index)}
            style={{ '--layer-index': index } as CSSProperties}
          >
            <span>0{index + 1}</span><Icon weight="duotone" /><strong>{title}</strong>
          </button>
        ))}
        <span className="layer-beam" aria-hidden="true" />
      </div>
      <div className="layer-detail" role="tabpanel">
        {(() => {
          const LayerIcon = layers[active].icon;
          return <LayerIcon weight="duotone" />;
        })()}
        <span>CAPA 0{active + 1}</span>
        <h2>{layers[active].title}</h2>
        <p>{layers[active].description}</p>
        <div className="layer-mini-flow">
          <Stack /><TreeStructure /><Code /><CheckCircle />
        </div>
      </div>
    </div>
  );
}
