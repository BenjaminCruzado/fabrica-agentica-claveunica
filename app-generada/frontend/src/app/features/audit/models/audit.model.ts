export interface AuditRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface AuditActionResult {
  updated: boolean;
  message?: string;
}
