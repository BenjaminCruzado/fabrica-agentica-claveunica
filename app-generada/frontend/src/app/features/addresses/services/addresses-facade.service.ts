import { Injectable } from '@angular/core';
import { FeatureApiService } from '../../../services/feature-api.service';

@Injectable({ providedIn: 'root' })
export class AddressesFacadeService {
  constructor(private api: FeatureApiService) {}
  execute(action: string, route: string) { return this.api.runFeatureAction('addresses', action, route); }
}
