export interface ProceduresRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface ProceduresActionResult {
  updated: boolean;
  message?: string;
}
