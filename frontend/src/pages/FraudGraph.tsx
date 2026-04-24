import { useState, useCallback, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  type NodeProps,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'
import { AlertTriangle, ExternalLink, Network } from 'lucide-react'
import { useGraph } from '../hooks/useGraph'
import RiskBadge from '../components/RiskBadge'
import type { GraphNode } from '../types'

const EDGE_COLORS: Record<string, string> = {
  shared_bank: '#ef4444',
  shared_device: '#f97316',
  shared_ip: '#eab308',
  shared_address: '#a855f7',
}

const NODE_BORDER_COLOR = (score: number, is_deceased: boolean) => {
  if (is_deceased) return '#1f2937'
  if (score >= 81) return '#ef4444'
  if (score >= 61) return '#f97316'
  if (score >= 31) return '#fbbf24'
  return '#22c55e'
}

function ApplicantNode({ data }: NodeProps) {
  const nodeData = data as GraphNode & { onClick: () => void }
  return (
    <div
      onClick={nodeData.onClick}
      className="cursor-pointer rounded-lg bg-white shadow-md border-2 px-3 py-2 min-w-[120px] text-center hover:shadow-lg transition-shadow"
      style={{ borderColor: NODE_BORDER_COLOR(nodeData.risk_score, nodeData.is_deceased) }}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-300" />
      {nodeData.is_deceased && <div className="text-xs text-red-600 font-bold mb-0.5">☠ DECEASED</div>}
      <div className="font-semibold text-gray-900 text-xs leading-tight">{nodeData.full_name}</div>
      <div className="mt-1 flex justify-center">
        <RiskBadge score={nodeData.risk_score} size="sm" />
      </div>
      {nodeData.ai_recommendation && (
        <div className={`text-[10px] mt-1 font-medium capitalize ${
          nodeData.ai_recommendation === 'deny' ? 'text-red-600' :
          nodeData.ai_recommendation === 'approve' ? 'text-green-600' : 'text-orange-600'
        }`}>
          {nodeData.ai_recommendation}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-gray-300" />
    </div>
  )
}

const nodeTypes = { applicant: ApplicantNode }

function layoutGraph(rawNodes: GraphNode[], rawEdges: ReturnType<typeof buildEdges>) {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 40 })

  rawNodes.forEach((n) => g.setNode(n.id, { width: 140, height: 80 }))
  rawEdges.forEach((e) => g.setEdge(e.source, e.target))
  dagre.layout(g)

  return rawNodes.map((n) => {
    const pos = g.node(n.id)
    return {
      id: n.id,
      type: 'applicant',
      position: { x: pos.x - 70, y: pos.y - 40 },
      data: n,
    }
  })
}

function buildEdges(edges: { source: string; target: string; relationship: string; weight: number }[]): Edge[] {
  return edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    label: e.relationship.replace('shared_', ''),
    style: { stroke: EDGE_COLORS[e.relationship] ?? '#94a3b8', strokeWidth: Math.min(e.weight, 4) },
    labelStyle: { fontSize: 10, fill: EDGE_COLORS[e.relationship] ?? '#64748b', fontWeight: 600 },
    labelBgStyle: { fill: 'white', fillOpacity: 0.8 },
    animated: e.relationship === 'shared_bank',
    type: 'smoothstep',
  }))
}

export default function FraudGraph() {
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

  const connectedNodeIds = useMemo(() => {
    const ids = new Set<string>()
    filteredEdges.forEach((e) => { ids.add(e.source); ids.add(e.target) })
    return ids
  }, [filteredEdges])

  const visibleNodes = useMemo(
    () => (data?.nodes ?? []).filter((n) => connectedNodeIds.has(n.id)),
    [data?.nodes, connectedNodeIds]
  )

  const rfNodes = useMemo(() => {
    const laid = layoutGraph(
      visibleNodes.map((n) => ({ ...n, onClick: () => setSelectedNode(n) })),
      filteredEdges
    )
    return laid as Node[]
  }, [visibleNodes, filteredEdges])

  const rfEdges = useMemo(() => buildEdges(filteredEdges), [filteredEdges])

  const [nodes, , onNodesChange] = useNodesState(rfNodes)
  const [edges, , onEdgesChange] = useEdgesState(rfEdges)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Network className="w-7 h-7 text-blue-600" /> Fraud Network Graph
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {visibleNodes.length} connected applicants · {filteredEdges.length} relationships
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <label className="text-gray-600 font-medium">Min Risk:</label>
            <input
              type="range" min={0} max={100} value={minRisk}
              onChange={(e) => setMinRisk(+e.target.value)}
              className="w-28"
            />
            <span className="font-bold text-gray-800 w-8">{minRisk}</span>
          </div>
        </div>
      </div>

      {/* Relationship toggles */}
      <div className="flex flex-wrap gap-3">
        {Object.entries(EDGE_COLORS).map(([rel, color]) => (
          <label key={rel} className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={relationshipFilter[rel] !== false}
              onChange={() => setRelationshipFilter((prev) => ({ ...prev, [rel]: !prev[rel] }))}
              className="rounded"
            />
            <span className="flex items-center gap-1.5 text-sm text-gray-700">
              <span className="w-3 h-1.5 rounded-full" style={{ backgroundColor: color }} />
              {rel.replace('shared_', '')}
            </span>
          </label>
        ))}
      </div>

      <div className="flex gap-4 h-[600px]">
        <div className="flex-1 rounded-xl border border-gray-200 overflow-hidden bg-white">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-gray-400">Loading graph...</div>
          ) : isError ? (
            <div className="flex items-center justify-center h-full text-red-500 gap-2">
              <AlertTriangle className="w-5 h-5" /> Failed to load graph data.
            </div>
          ) : visibleNodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-400 text-center p-8">
              <div>
                <Network className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No connected fraud networks detected</p>
                <p className="text-sm mt-1">Try lowering the minimum risk threshold.</p>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              onNodeClick={(_, node) => setSelectedNode(node.data as GraphNode)}
            >
              <Background gap={16} color="#f0f0f0" />
              <Controls />
              <MiniMap nodeColor={(n) => NODE_BORDER_COLOR((n.data as GraphNode).risk_score, (n.data as GraphNode).is_deceased)} />
            </ReactFlow>
          )}
        </div>

        {/* Node detail sidebar */}
        {selectedNode && (
          <div className="w-64 bg-white rounded-xl border border-gray-200 p-4 flex-shrink-0">
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-bold text-gray-900 text-sm">{selectedNode.full_name}</h3>
              <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
            </div>
            {selectedNode.is_deceased && (
              <div className="mb-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded px-2 py-1 font-semibold">
                ☠ Flagged as Deceased
              </div>
            )}
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Risk Score</span>
                <RiskBadge score={selectedNode.risk_score} size="sm" />
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <span className="capitalize text-gray-700 font-medium">{selectedNode.status.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Program</span>
                <span className="capitalize text-gray-700 font-medium">{selectedNode.program_type}</span>
              </div>
              {selectedNode.ai_recommendation && (
                <div className="flex justify-between">
                  <span className="text-gray-500">AI Rec</span>
                  <span className={`capitalize font-medium ${
                    selectedNode.ai_recommendation === 'deny' ? 'text-red-600' :
                    selectedNode.ai_recommendation === 'approve' ? 'text-green-600' : 'text-orange-600'
                  }`}>{selectedNode.ai_recommendation}</span>
                </div>
              )}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Link
                to={`/applications/${selectedNode.id}`}
                className="flex items-center justify-center gap-2 w-full py-2 px-4 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
              >
                View Full Application <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-gray-500">
        <span className="font-semibold text-gray-600">Node border color:</span>
        {[
          { label: 'Low risk (0-30)', color: '#22c55e' },
          { label: 'Medium (31-60)', color: '#fbbf24' },
          { label: 'High (61-80)', color: '#f97316' },
          { label: 'Critical (81-100)', color: '#ef4444' },
          { label: 'Deceased', color: '#1f2937' },
        ].map(({ label, color }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full border-2" style={{ borderColor: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
