import { useRef, useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import * as d3 from 'd3'
import { AlertTriangle, Network, ExternalLink } from 'lucide-react'
import { useGraph } from '../hooks/useGraph'
import RiskBadge from '../components/RiskBadge'
import type { GraphNode, GraphEdge } from '../types'

type SimNode = GraphNode & d3.SimulationNodeDatum
type SimLink = Omit<GraphEdge, 'source' | 'target'> & {
  source: string | SimNode
  target: string | SimNode
}

const EDGE_COLORS: Record<string, string> = {
  shared_bank: '#f87171',
  shared_device: '#fb923c',
  shared_ip: '#facc15',
  shared_address: '#c084fc',
}

function nodeColor(score: number, deceased: boolean): string {
  if (deceased) return '#475569'
  if (score >= 81) return '#ef4444'
  if (score >= 61) return '#f97316'
  if (score >= 31) return '#fbbf24'
  return '#4ade80'
}

function nodeRadius(score: number): number {
  return 14 + (score / 100) * 8
}

function abbrevName(full: string): string {
  const parts = full.trim().split(' ')
  if (parts.length === 1) return full
  return `${parts[0][0]}. ${parts[parts.length - 1]}`
}

export default function FraudGraph() {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const simRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null)

  const [minRisk, setMinRisk] = useState(40)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [relationshipFilter, setRelationshipFilter] = useState<Record<string, boolean>>({
    shared_bank: true,
    shared_device: true,
    shared_ip: true,
    shared_address: true,
  })

  const { data, isLoading, isError } = useGraph({ min_risk: minRisk })

  const filteredEdges = useMemo(
    () => (data?.edges ?? []).filter((e) => relationshipFilter[e.relationship] !== false),
    [data?.edges, relationshipFilter]
  )

  const connectedIds = useMemo(() => {
    const ids = new Set<string>()
    filteredEdges.forEach((e) => { ids.add(e.source); ids.add(e.target) })
    return ids
  }, [filteredEdges])

  const visibleNodes = useMemo(
    () => (data?.nodes ?? []).filter((n) => connectedIds.has(n.id)),
    [data?.nodes, connectedIds]
  )

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return
    if (visibleNodes.length === 0) return

    const W = containerRef.current.clientWidth
    const H = containerRef.current.clientHeight

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    svg.attr('width', W).attr('height', H)

    // Glow filter
    const defs = svg.append('defs')
    const filter = defs.append('filter').attr('id', 'glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%')
    filter.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '4').attr('result', 'blur')
    const merge = filter.append('feMerge')
    merge.append('feMergeNode').attr('in', 'blur')
    merge.append('feMergeNode').attr('in', 'SourceGraphic')

    // Arrow marker (not really needed for undirected, but adds polish for bank edges)
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 5)
      .attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#f87171')
      .attr('opacity', 0.5)

    // Background
    svg.append('rect').attr('width', W).attr('height', H).attr('fill', '#0f172a')

    // Subtle grid
    const gridG = svg.append('g').attr('opacity', 0.04)
    for (let x = 0; x < W; x += 40) gridG.append('line').attr('x1', x).attr('y1', 0).attr('x2', x).attr('y2', H).attr('stroke', '#94a3b8')
    for (let y = 0; y < H; y += 40) gridG.append('line').attr('x1', 0).attr('y1', y).attr('x2', W).attr('y2', y).attr('stroke', '#94a3b8')

    const g = svg.append('g')

    // Zoom + pan
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => g.attr('transform', event.transform))
    svg.call(zoom)
    svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2, H / 2).scale(1))

    // Data
    const nodes: SimNode[] = visibleNodes.map((n) => ({ ...n }))
    const links: SimLink[] = filteredEdges.map((e) => ({ ...e }))

    // Force simulation
    const simulation = d3.forceSimulation<SimNode>(nodes)
      .force('link', d3.forceLink<SimNode, SimLink>(links).id((d) => d.id).distance(120).strength(0.4))
      .force('charge', d3.forceManyBody<SimNode>().strength(-400).distanceMax(400))
      .force('center', d3.forceCenter(0, 0))
      .force('collision', d3.forceCollide<SimNode>().radius((d) => nodeRadius(d.risk_score) + 10))
      .alphaDecay(0.02)

    simRef.current = simulation

    // Edge lines
    const linkG = g.append('g')
    const linkEl = linkG.selectAll<SVGLineElement, SimLink>('line')
      .data(links)
      .join('line')
      .attr('stroke', (d) => EDGE_COLORS[d.relationship] ?? '#64748b')
      .attr('stroke-opacity', 0.45)
      .attr('stroke-width', (d) => Math.max(1.5, d.weight * 0.7))
      .attr('stroke-linecap', 'round')
      .attr('marker-end', (d) => d.relationship === 'shared_bank' ? 'url(#arrowhead)' : null)

    // Edge labels (only show on hover would be ideal; shown statically for demo)
    const linkLabelEl = linkG.selectAll<SVGTextElement, SimLink>('text')
      .data(links)
      .join('text')
      .attr('fill', (d) => EDGE_COLORS[d.relationship] ?? '#94a3b8')
      .attr('font-size', 9)
      .attr('font-family', 'monospace')
      .attr('text-anchor', 'middle')
      .attr('opacity', 0.65)
      .text((d) => d.relationship.replace('shared_', ''))

    // Node groups
    const nodeG = g.append('g')
    const nodeEl = nodeG.selectAll<SVGGElement, SimNode>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        setSelectedNode({ ...d })
      })

    // Drag
    nodeEl.call(
      d3.drag<SVGGElement, SimNode>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
    )

    // Glow halo
    nodeEl.append('circle')
      .attr('r', (d) => nodeRadius(d.risk_score) + 7)
      .attr('fill', (d) => nodeColor(d.risk_score, d.is_deceased))
      .attr('opacity', 0.15)
      .attr('filter', 'url(#glow)')

    // Outer ring
    nodeEl.append('circle')
      .attr('r', (d) => nodeRadius(d.risk_score) + 2)
      .attr('fill', 'none')
      .attr('stroke', (d) => nodeColor(d.risk_score, d.is_deceased))
      .attr('stroke-width', 1.5)
      .attr('opacity', 0.4)

    // Main node circle
    nodeEl.append('circle')
      .attr('r', (d) => nodeRadius(d.risk_score))
      .attr('fill', (d) => nodeColor(d.risk_score, d.is_deceased))
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.25)

    // Risk score inside
    nodeEl.append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 11)
      .attr('font-weight', 700)
      .attr('fill', 'white')
      .text((d) => d.risk_score)

    // Skull for deceased
    nodeEl.filter((d) => d.is_deceased)
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('y', (d) => -(nodeRadius(d.risk_score) + 10))
      .attr('font-size', 13)
      .text('☠')

    // Name label below
    nodeEl.append('text')
      .attr('text-anchor', 'middle')
      .attr('y', (d) => nodeRadius(d.risk_score) + 14)
      .attr('font-size', 10)
      .attr('font-weight', 500)
      .attr('fill', '#cbd5e1')
      .text((d) => abbrevName(d.full_name))

    // Hover highlight
    nodeEl
      .on('mouseenter', function (_, d) {
        d3.select(this).select('circle:nth-child(3)')
          .transition().duration(150)
          .attr('r', nodeRadius(d.risk_score) + 3)
          .attr('stroke-opacity', 0.7)
      })
      .on('mouseleave', function (_, d) {
        d3.select(this).select('circle:nth-child(3)')
          .transition().duration(150)
          .attr('r', nodeRadius(d.risk_score))
          .attr('stroke-opacity', 0.25)
      })

    // Tick
    simulation.on('tick', () => {
      linkEl
        .attr('x1', (d) => (d.source as SimNode).x!)
        .attr('y1', (d) => (d.source as SimNode).y!)
        .attr('x2', (d) => (d.target as SimNode).x!)
        .attr('y2', (d) => (d.target as SimNode).y!)

      linkLabelEl
        .attr('x', (d) => ((d.source as SimNode).x! + (d.target as SimNode).x!) / 2)
        .attr('y', (d) => ((d.source as SimNode).y! + (d.target as SimNode).y!) / 2 - 5)

      nodeEl.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })

    // Click background to deselect
    svg.on('click', () => setSelectedNode(null))

    return () => {
      simulation.stop()
      svg.on('click', null)
    }
  }, [visibleNodes, filteredEdges])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Network className="w-7 h-7 text-blue-600" /> Fraud Network Graph
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {visibleNodes.length} connected applicants · {filteredEdges.length} relationships
            <span className="ml-2 text-xs text-gray-400">· drag nodes · scroll to zoom</span>
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <label className="text-gray-600 font-medium">Min Risk</label>
          <input
            type="range" min={0} max={100} value={minRisk}
            onChange={(e) => setMinRisk(+e.target.value)}
            className="w-28 accent-blue-600"
          />
          <span className="font-bold text-gray-800 w-8 tabular-nums">{minRisk}</span>
        </div>
      </div>

      {/* Relationship toggles */}
      <div className="flex flex-wrap gap-4">
        {Object.entries(EDGE_COLORS).map(([rel, color]) => (
          <label key={rel} className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={relationshipFilter[rel] !== false}
              onChange={() => setRelationshipFilter((prev) => ({ ...prev, [rel]: !prev[rel] }))}
              className="rounded"
            />
            <span className="flex items-center gap-1.5 text-sm text-gray-700">
              <span className="w-4 h-1.5 rounded-full inline-block" style={{ backgroundColor: color }} />
              {rel.replace('shared_', '')}
            </span>
          </label>
        ))}
      </div>

      <div className="flex gap-4" style={{ height: 580 }}>
        {/* Graph canvas */}
        <div ref={containerRef} className="flex-1 rounded-xl overflow-hidden relative" style={{ background: '#0f172a' }}>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm gap-2">
              <span className="animate-spin text-xl">🕸</span> Building graph…
            </div>
          )}
          {isError && (
            <div className="absolute inset-0 flex items-center justify-center text-red-400 gap-2 text-sm">
              <AlertTriangle className="w-5 h-5" /> Failed to load graph data.
            </div>
          )}
          {!isLoading && !isError && visibleNodes.length === 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 text-center p-8 gap-3">
              <Network className="w-12 h-12 text-slate-600" />
              <p className="font-medium">No fraud networks at this risk threshold</p>
              <p className="text-sm text-slate-500">Lower the minimum risk slider to reveal connections.</p>
            </div>
          )}
          <svg ref={svgRef} className="w-full h-full" />
        </div>

        {/* Node detail sidebar */}
        {selectedNode && (
          <div className="w-60 bg-white rounded-xl border border-gray-200 p-4 flex-shrink-0 flex flex-col">
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-bold text-gray-900 text-sm leading-tight">{selectedNode.full_name}</h3>
              <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-gray-600 text-lg leading-none ml-2">×</button>
            </div>
            {selectedNode.is_deceased && (
              <div className="mb-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded px-2 py-1 font-semibold">
                ☠ Flagged as Deceased
              </div>
            )}
            <div className="space-y-2 text-sm flex-1">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Risk Score</span>
                <RiskBadge score={selectedNode.risk_score} size="sm" />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <span className="capitalize text-gray-700 font-medium text-xs">{selectedNode.status.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Program</span>
                <span className="capitalize text-gray-700 font-medium text-xs">{selectedNode.program_type}</span>
              </div>
              {selectedNode.ai_recommendation && (
                <div className="flex justify-between">
                  <span className="text-gray-500">AI Rec</span>
                  <span className={`capitalize font-semibold text-xs ${
                    selectedNode.ai_recommendation === 'deny' ? 'text-red-600' :
                    selectedNode.ai_recommendation === 'approve' ? 'text-green-600' : 'text-orange-600'
                  }`}>
                    {selectedNode.ai_recommendation}
                  </span>
                </div>
              )}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Link
                to={`/applications/${selectedNode.id}`}
                className="flex items-center justify-center gap-2 w-full py-2 px-3 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
              >
                View Application <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-gray-500">
        <span className="font-semibold text-gray-600">Node color:</span>
        {[
          { label: 'Low (0–30)', color: '#4ade80' },
          { label: 'Medium (31–60)', color: '#fbbf24' },
          { label: 'High (61–80)', color: '#f97316' },
          { label: 'Critical (81–100)', color: '#ef4444' },
          { label: 'Deceased', color: '#475569' },
        ].map(({ label, color }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
            {label}
          </span>
        ))}
        <span className="ml-2 text-gray-400">· Node size scales with risk score</span>
      </div>
    </div>
  )
}
