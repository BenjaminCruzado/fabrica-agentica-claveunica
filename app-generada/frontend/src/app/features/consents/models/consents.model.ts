export interface ConsentsRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface ConsentsActionResult {
  updated: boolean;
  message?: string;
}
