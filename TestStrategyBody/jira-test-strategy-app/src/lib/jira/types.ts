export interface JiraIssue {
  key: string;
  summary: string;
  description: string | null;
  issueType: string;
  priority: string;
  status: string;
  labels: string[];
  components: string[];
}
