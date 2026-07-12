export interface AddressesRecord {
  primary: string;
  secondary: string;
  status: string;
}

export interface AddressesActionResult {
  updated: boolean;
  message?: string;
}
