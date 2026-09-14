export interface LabSummary {
  id: string;
  version: string;
  title: string;
  track: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'production';
  estimated_minutes: number;
  validation_status: string;
  objectives: string[];
}

export interface Hint {
  tier: number;
  title: string;
  content: string;
  penalty_points: number;
}

export interface Task {
  id: string;
  order: number;
  title: string;
  description: string;
  hints: Hint[];
}

export interface TopologyNode {
  id: string;
  label: string;
  type: string;
  status: 'healthy' | 'degraded' | 'failed' | 'slow' | 'unknown';
}

export interface TopologyEdge {
  source: string;
  target: string;
  label?: string;
  protocol?: string;
  status: 'normal' | 'slow' | 'broken' | 'dropped';
}

export interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface LabDetail extends LabSummary {
  what_why: string;
  architecture_overview: string;
  internals_deep_dive: string;
  common_errors: string[];
  troubleshooting_workflow: string[];
  tasks: Task[];
  topology?: TopologyData;
  initial_state?: {
    files?: { path: string; content: string }[];
  };
}

export interface ValidationItem {
  rule_id: string;
  rule_type: string;
  description: string;
  passed: boolean;
  score_awarded: number;
  max_score: number;
  feedback: string;
}

export interface ValidationReport {
  overall_status: 'PASS' | 'PARTIAL' | 'FAIL';
  total_score: number;
  max_possible_score: number;
  percentage: number;
  items: ValidationItem[];
  summary: string;
}

export interface IncidentSummary {
  id: string;
  title: string;
  severity: 'SEV-1' | 'SEV-2';
  summary: string;
  impact: string;
  affected_services: string[];
}

export interface AlertEvent {
  id: string;
  name: string;
  severity: string;
  status: string;
  started_at: string;
  description: string;
}

export interface IncidentHypothesis {
  id: string;
  statement: string;
  plausible: boolean;
  evidence_required: string;
  disproven_by?: string;
}

export interface IncidentDetail extends IncidentSummary {
  initial_symptoms: string[];
  topology: TopologyData;
  alerts: AlertEvent[];
  hypotheses: IncidentHypothesis[];
  diagnostic_commands: { cmd: string; description: string }[];
}

export interface IncidentScore {
  detection_score: number;
  investigation_score: number;
  root_cause_score: number;
  fix_score: number;
  verification_score: number;
  prevention_score: number;
  total_score: number;
  feedback: string[];
}

export interface DashboardData {
  user: {
    username: string;
    role: string;
    overall_mastery: number;
    troubleshooting_rating: string;
    labs_completed: number;
    incidents_resolved: number;
    average_incident_score: number;
  };
  radar: { technology: string; mastery: number; labs_count: number }[];
  weak_areas: { topic: string; track: string; severity: string; recommendation: string }[];
  recent_activity: { type: string; id: string; title: string; score: number; timestamp: string }[];
  recommended_next: { type: string; id: string; title: string; track: string; reason: string };
}
