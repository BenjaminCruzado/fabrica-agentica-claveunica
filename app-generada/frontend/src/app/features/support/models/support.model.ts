export interface SupportRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface SupportActionResult {
  updated: boolean;
  message?: string;
}
