export interface ProfileRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface ProfileActionResult {
  updated: boolean;
  message?: string;
}
