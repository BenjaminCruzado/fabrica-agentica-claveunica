export interface CasesRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface CasesActionResult {
  updated: boolean;
  message?: string;
}
