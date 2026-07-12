export interface SecurityRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface SecurityActionResult {
  updated: boolean;
  message?: string;
}
