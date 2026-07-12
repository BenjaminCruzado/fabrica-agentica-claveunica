export interface NotificationsRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface NotificationsActionResult {
  updated: boolean;
  message?: string;
}
