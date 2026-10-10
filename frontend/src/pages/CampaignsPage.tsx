import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { EmptyState } from "../components/EmptyState";
import { ErrorBanner } from "../components/ErrorBanner";
import { Skeleton } from "../components/Skeleton";
import { StatusBadge } from "../components/StatusBadge";
import { useAsync } from "../hooks/useAsync";
import { relationshipLabel } from "../lib/format";
import { api } from "../services/api";
import type { CampaignDetail, Relationship } from "../types/api";

export function CampaignsPage() {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const list = useAsync(() => api.campaigns(), []);
  const selectedId = campaignId ?? list.data?.[0]?.id;
  const detail = useAsync(
    () => (selectedId ? api.campaign(selectedId) : Promise.resolve(null)),
    [selectedId],
  );
  const [selectedRel, setSelectedRel] = useState<Relationship | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    if (!campaignId && list.data?.[0]?.id) {
      navigate(`/campaigns/${list.data[0].id}`, { replace: true });
    }
  }, [campaignId, list.data, navigate]);

  if (list.loading) return <Skeleton className="h-96" />;
  if (list.error) return <ErrorBanner message={list.error} onRetry={list.reload} />;
  if (!list.data?.length) {
    return <EmptyState title="No campaign clusters" body="Relationships appear after advertisements share entities or similar text." />;
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Campaign intelligence</h1>
        <p className="mt-1 text-sm text-mute">
          Clusters are connected components of stored relationship evidence. Edges are not drawn without that evidence.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {list.data.map((campaign) => (
          <Link
            key={campaign.id}
            to={`/campaigns/${campaign.id}`}
            className={`rounded border px-3 py-1 text-sm ${
              campaign.id === selectedId ? "border-accent text-accent" : "border-line text-mute"
            }`}
          >
            {campaign.member_count} ads · max {campaign.max_risk_score}
          </Link>
        ))}
      </div>
      {detail.loading ? <Skeleton className="h-[520px]" /> : null}
      {detail.error ? <ErrorBanner message={detail.error} onRetry={detail.reload} /> : null}
      {detail.data ? (
        <GraphPanel
          campaign={detail.data}
          selectedRel={selectedRel}
          selectedNode={selectedNode}
          onSelectRel={setSelectedRel}
          onSelectNode={setSelectedNode}
        />
      ) : null}
    </div>
  );
}

function GraphPanel({
  campaign,
  selectedRel,
  selectedNode,
  onSelectRel,
  onSelectNode,
}: {
  campaign: CampaignDetail;
  selectedRel: Relationship | null;
  selectedNode: string | null;
  onSelectRel: (rel: Relationship | null) => void;
  onSelectNode: (id: string | null) => void;
}) {
  const ads = useMemo(() => Object.fromEntries(campaign.advertisements.map((ad) => [ad.id, ad])), [campaign]);
  const nodes: Node[] = useMemo(
    () =>
      campaign.advertisements.map((ad, index) => ({
        id: ad.id,
        position: {
          x: 180 * Math.cos((index / campaign.advertisements.length) * Math.PI * 2),
          y: 180 * Math.sin((index / campaign.advertisements.length) * Math.PI * 2),
        },
        data: { label: `${ad.risk_category} ${ad.risk_score}` },
        style: {
          background: "#111318",
          color: "#F5F5F5",
          border: `1px solid ${ad.risk_score >= 50 ? "#F43F5E" : "#3EE0FF"}`,
          fontSize: 12,
          width: 120,
        },
      })),
    [campaign],
  );
  const edges: Edge[] = useMemo(
    () =>
      campaign.relationships.map((rel) => ({
        id: rel.id,
        source: rel.source_ad_id,
        target: rel.target_ad_id,
        label: relationshipLabel(rel.relationship_type),
        markerEnd: { type: MarkerType.ArrowClosed, color: "#8B929E" },
        style: {
          stroke: rel.relationship_type === "text_similarity" ? "#F59E0B" : "#3EE0FF",
          strokeDasharray: rel.relationship_type === "text_similarity" ? "6 4" : undefined,
        },
        labelStyle: { fill: "#8B929E", fontSize: 10 },
      })),
    [campaign],
  );
  const selectedAd = selectedNode ? ads[selectedNode] : null;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="h-[540px] overflow-hidden rounded-lg border border-line bg-panel lg:col-span-2">
        <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          colorMode="dark"
          onNodeClick={(_, node) => {
            onSelectNode(node.id);
            onSelectRel(null);
          }}
          onEdgeClick={(_, edge) => {
            const rel = campaign.relationships.find((item) => item.id === edge.id) ?? null;
            onSelectRel(rel);
            onSelectNode(null);
          }}
        >
          <Background color="#1E232C" />
          <MiniMap pannable style={{ background: "#08090B" }} />
          <Controls />
        </ReactFlow>
        </ReactFlowProvider>
      </div>
      <aside className="space-y-4 rounded-lg border border-line bg-panel p-4">
        <div>
          <h2 className="text-sm font-medium">Legend</h2>
          <ul className="mt-2 space-y-1 text-xs text-mute">
            <li>Cyan solid edge: observed shared entity</li>
            <li>Amber dashed edge: inferred text similarity</li>
            <li>Red node border: high or critical triage score</li>
          </ul>
        </div>
        {selectedAd ? (
          <div>
            <h3 className="text-sm font-medium">Selected advertisement</h3>
            <StatusBadge value={selectedAd.risk_category} />
            <p className="mt-2 line-clamp-5 text-sm">{selectedAd.text}</p>
            <Link className="mt-3 inline-block text-sm text-accent" to={`/investigations/${selectedAd.id}`}>
              Open investigation
            </Link>
          </div>
        ) : null}
        {selectedRel ? (
          <div>
            <h3 className="text-sm font-medium">Relationship evidence</h3>
            <p className="mt-2 text-sm">{relationshipLabel(selectedRel.relationship_type)}</p>
            <p className="mt-1 text-sm text-mute">{selectedRel.explanation}</p>
            <p className="mt-2 font-mono text-[11px]">{selectedRel.evidence}</p>
            {selectedRel.similarity_score != null ? (
              <p className="mt-2 text-xs text-mute">Similarity score {selectedRel.similarity_score} (inferred, not an observed identifier).</p>
            ) : (
              <p className="mt-2 text-xs text-mute">Observed shared identifier. This is not proof of common ownership.</p>
            )}
          </div>
        ) : null}
        {!selectedAd && !selectedRel ? (
          <p className="text-sm text-mute">Select a node or edge to inspect evidence.</p>
        ) : null}
      </aside>
    </div>
  );
}
